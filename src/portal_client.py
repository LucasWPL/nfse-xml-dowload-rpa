import re
import time
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import PORTAL_DATE_FORMAT, Settings
from .logger import AppLogger
from .models import DownloadEntry

LOGIN_URL = "https://www.nfse.gov.br/EmissorNacional/Login"
NOTAS_EMITIDAS_URL = "https://www.nfse.gov.br/EmissorNacional/Notas/Emitidas"

DOWNLOAD_LINK_XPATH = (
    "//a[contains(@href, '/Download/') and "
    "(contains(@class, 'list-group-item') or contains(@href, 'NFSe') or contains(@href, 'DANFSe'))]"
)

START_DATE_SELECTORS = [
    (By.NAME, "DataInicial"),
    (By.ID, "DataInicial"),
    (By.NAME, "DataEmissaoInicial"),
    (By.ID, "DataEmissaoInicial"),
    (By.NAME, "dtInicio"),
    (By.ID, "dtInicio"),
    (By.NAME, "datainicio"),
    (By.ID, "datainicio"),
    (By.CSS_SELECTOR, "input[placeholder*='Inicial']"),
    (By.CSS_SELECTOR, "input[placeholder*='inicial']"),
    (
        By.XPATH,
        "//label[contains(normalize-space(.), 'Data Inicial')]/following::input[1]",
    ),
]

END_DATE_SELECTORS = [
    (By.NAME, "DataFinal"),
    (By.ID, "DataFinal"),
    (By.NAME, "DataEmissaoFinal"),
    (By.ID, "DataEmissaoFinal"),
    (By.NAME, "dtFim"),
    (By.ID, "dtFim"),
    (By.NAME, "datafim"),
    (By.ID, "datafim"),
    (By.CSS_SELECTOR, "input[placeholder*='Final']"),
    (By.CSS_SELECTOR, "input[placeholder*='final']"),
    (
        By.XPATH,
        "//label[contains(normalize-space(.), 'Data Final')]/following::input[1]",
    ),
]

SEARCH_BUTTON_SELECTORS = [
    (By.XPATH, "//button[contains(normalize-space(.), 'Consultar')]"),
    (By.XPATH, "//button[contains(normalize-space(.), 'Pesquisar')]"),
    (By.XPATH, "//button[contains(normalize-space(.), 'Filtrar')]"),
    (By.XPATH, "//input[@type='submit']"),
]

NEXT_PAGE_SELECTORS = [
    (By.XPATH, "//a[@rel='next' and not(contains(@class, 'disabled'))]"),
    (
        By.XPATH,
        "//a[contains(normalize-space(.), 'Próxima') and not(contains(@class, 'disabled'))]",
    ),
    (
        By.XPATH,
        "//a[contains(normalize-space(.), 'Proxima') and not(contains(@class, 'disabled'))]",
    ),
    (
        By.XPATH,
        "//a[contains(@aria-label, 'Próxima') and not(contains(@class, 'disabled'))]",
    ),
]

LOGIN_USERNAME_SELECTORS = [
    (By.NAME, "Inscricao"),
    (By.ID, "Inscricao"),
    (By.NAME, "Login"),
    (By.ID, "Login"),
    (By.NAME, "Usuario"),
    (By.ID, "Usuario"),
    (By.CSS_SELECTOR, "input[name*='inscricao' i]"),
    (By.CSS_SELECTOR, "input[id*='inscricao' i]"),
    (By.CSS_SELECTOR, "input[placeholder*='inscri' i]"),
    (By.CSS_SELECTOR, "input[placeholder*='cpf' i]"),
    (
        By.XPATH,
        "//label[contains(translate(normalize-space(.), 'INSCRIÇAO', 'inscricao'), 'inscricao')]/following::input[1]",
    ),
    (
        By.XPATH,
        "//label[contains(translate(normalize-space(.), 'USUÁRIO', 'usuario'), 'usuario')]/following::input[1]",
    ),
]

LOGIN_PASSWORD_SELECTORS = [
    (By.NAME, "Senha"),
    (By.ID, "Senha"),
    (By.CSS_SELECTOR, "input[type='password']"),
    (By.CSS_SELECTOR, "input[name*='senha' i]"),
    (By.CSS_SELECTOR, "input[id*='senha' i]"),
    (
        By.XPATH,
        "//label[contains(translate(normalize-space(.), 'SENHA', 'senha'), 'senha')]/following::input[1]",
    ),
]

LOGIN_BUTTON_SELECTORS = [
    (By.XPATH, "//button[contains(normalize-space(.), 'Entrar')]"),
    (By.XPATH, "//button[contains(normalize-space(.), 'Acessar')]"),
    (By.XPATH, "//button[contains(normalize-space(.), 'Login')]"),
    (By.XPATH, "//input[@type='submit']"),
]


def normalize_field_value(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def field_value_matches(actual: str, expected: str) -> bool:
    if (actual or "").strip() == (expected or "").strip():
        return True

    normalized_actual = normalize_field_value(actual)
    normalized_expected = normalize_field_value(expected)

    if normalized_actual and normalized_expected:
        return normalized_actual == normalized_expected

    return False


class PortalClient:
    def __init__(self, driver: webdriver.Chrome, settings: Settings, logger: AppLogger) -> None:
        self.driver = driver
        self.settings = settings
        self.logger = logger

    def wait_for_any(self, locators: list[tuple[str, str]], timeout: int | None = None) -> bool:
        end_time = time.time() + (timeout or self.settings.wait_timeout)
        while time.time() < end_time:
            for by, selector in locators:
                if self.driver.find_elements(by, selector):
                    return True
            time.sleep(0.5)
        return False

    def element_summary(self, element: WebElement) -> str:
        attrs = {
            "tag": element.tag_name,
            "id": element.get_attribute("id") or "",
            "name": element.get_attribute("name") or "",
            "type": element.get_attribute("type") or "",
            "placeholder": element.get_attribute("placeholder") or "",
            "value": element.get_attribute("value") or "",
        }
        return ", ".join(f"{key}={value!r}" for key, value in attrs.items())

    def find_first_visible(self, selectors: list[tuple[str, str]]) -> tuple[WebElement, str]:
        for by, selector in selectors:
            elements = self.driver.find_elements(by, selector)
            for element in elements:
                if element.is_displayed():
                    return element, f"{by}={selector}"
        raise RuntimeError(f"Elemento não encontrado para os seletores: {selectors}")

    def set_input_value(self, element: WebElement, value: str) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )
        self.driver.execute_script("arguments[0].removeAttribute('readonly');", element)

        try:
            element.click()
            time.sleep(0.2)
            element.send_keys(Keys.CONTROL, "a")
            element.send_keys(Keys.DELETE)
            element.send_keys(value)
            element.send_keys(Keys.TAB)
            time.sleep(0.2)
        except Exception:
            pass

        current_value = (element.get_attribute("value") or "").strip()
        if field_value_matches(current_value, value):
            return

        self.driver.execute_script(
            """
            const element = arguments[0];
            const value = arguments[1];
            const descriptor = Object.getOwnPropertyDescriptor(
                Object.getPrototypeOf(element),
                'value'
            );

            if (descriptor && descriptor.set) {
                descriptor.set.call(element, value);
            } else {
                element.value = value;
            }

            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
            """,
            element,
            value,
        )

        current_value = (element.get_attribute("value") or "").strip()
        if not field_value_matches(current_value, value):
            raise RuntimeError(
                f"Não foi possível preencher o campo com {value!r}. Campo localizado: {self.element_summary(element)}"
            )

    def click_first_available(self, selectors: list[tuple[str, str]], description: str) -> bool:
        for by, selector in selectors:
            elements = self.driver.find_elements(by, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    self.logger.debug(
                        f"{description} localizado por {by}={selector}: {self.element_summary(element)}"
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});",
                        element,
                    )
                    time.sleep(0.2)
                    element.click()
                    return True
        return False

    def login(self) -> None:
        try:
            self.driver.get(LOGIN_URL)
            WebDriverWait(self.driver, self.settings.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            if not self.settings.nfse_username or not self.settings.nfse_password:
                raise RuntimeError("Defina NFSE_USERNAME e NFSE_PASSWORD no .env do projeto.")

            username_input, username_selector = self.find_first_visible(LOGIN_USERNAME_SELECTORS)
            password_input, password_selector = self.find_first_visible(LOGIN_PASSWORD_SELECTORS)

            self.logger.debug(
                f"Campo de usuário localizado por {username_selector}: {self.element_summary(username_input)}"
            )
            self.logger.debug(
                f"Campo de senha localizado por {password_selector}: {self.element_summary(password_input)}"
            )

            self.set_input_value(username_input, self.settings.nfse_username)
            self.set_input_value(password_input, self.settings.nfse_password)

            previous_url = self.driver.current_url
            clicked = self.click_first_available(LOGIN_BUTTON_SELECTORS, "Botao de login")

            if not clicked:
                form = self.driver.execute_script(
                    "return arguments[0].form || arguments[1].form;",
                    username_input,
                    password_input,
                )
                if not form:
                    raise RuntimeError("Não foi possível localizar o botão ou formulário de login.")
                self.logger.debug("Botão de login não encontrado. Enviando formulário como fallback.")
                self.driver.execute_script("arguments[0].requestSubmit();", form)

            WebDriverWait(self.driver, self.settings.wait_timeout).until(
                lambda current_driver: current_driver.current_url != previous_url
                or "login" not in current_driver.current_url.lower()
            )

            if "login" in self.driver.current_url.lower():
                raise RuntimeError("Login não foi concluído com sucesso. A página permaneceu na rota de login.")

            time.sleep(2)
        except Exception as exc:
            raise RuntimeError(f"Erro no login: {exc}") from exc

    def navigate_to_notas_emitidas(self) -> None:
        try:
            self.driver.get(NOTAS_EMITIDAS_URL)
            WebDriverWait(self.driver, self.settings.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as exc:
            raise RuntimeError(f"Erro ao navegar para 'Notas Emitidas': {exc}") from exc

    def apply_date_filter(self, start_date: date, end_date: date) -> None:
        start_input, start_selector = self.find_first_visible(START_DATE_SELECTORS)
        end_input, end_selector = self.find_first_visible(END_DATE_SELECTORS)

        start_value = start_date.strftime(PORTAL_DATE_FORMAT)
        end_value = end_date.strftime(PORTAL_DATE_FORMAT)

        self.set_input_value(start_input, start_value)
        self.set_input_value(end_input, end_value)

        self.logger.debug(
            f"Campo inicial localizado por {start_selector}: {self.element_summary(start_input)}"
        )
        self.logger.debug(
            f"Campo final localizado por {end_selector}: {self.element_summary(end_input)}"
        )

        previous_url = self.driver.current_url
        clicked = self.click_first_available(SEARCH_BUTTON_SELECTORS, "Botao de consulta")

        if not clicked:
            form = self.driver.execute_script(
                "return arguments[0].form || arguments[1].form;",
                start_input,
                end_input,
            )
            if form:
                self.logger.debug("Botão de consulta não encontrado. Enviando formulário como fallback.")
                self.driver.execute_script("arguments[0].requestSubmit();", form)
            else:
                raise RuntimeError("Não foi possível localizar o botão de consulta da tela.")

        try:
            WebDriverWait(self.driver, self.settings.wait_timeout).until(
                lambda current_driver: current_driver.current_url != previous_url
                or current_driver.find_elements(By.CLASS_NAME, "sem-registros")
                or current_driver.find_elements(By.XPATH, DOWNLOAD_LINK_XPATH)
            )
        except TimeoutException:
            time.sleep(3)

    def extract_note_date(self, text: str) -> date | None:
        for raw_match in re.findall(r"\b\d{2}/\d{2}/\d{4}\b", text):
            try:
                return datetime.strptime(raw_match, PORTAL_DATE_FORMAT).date()
            except ValueError:
                continue
        return None

    def extract_download_key(self, url: str) -> str | None:
        query = parse_qs(urlparse(url).query)
        for key in ("chave", "id", "numero", "codigo"):
            values = query.get(key)
            if values:
                return values[0]
        return None

    def collect_download_entries(self) -> list[DownloadEntry]:
        entries: list[DownloadEntry] = []
        seen_urls: set[str] = set()
        visited_pages: set[str] = set()

        while True:
            self.wait_for_any(
                [
                    (By.CLASS_NAME, "sem-registros"),
                    (By.XPATH, DOWNLOAD_LINK_XPATH),
                ]
            )

            if self.driver.find_elements(By.CLASS_NAME, "sem-registros"):
                break

            current_url = self.driver.current_url
            if current_url in visited_pages:
                break
            visited_pages.add(current_url)

            for link in self.driver.find_elements(By.XPATH, DOWNLOAD_LINK_XPATH):
                href = link.get_attribute("href")
                if not href or href in seen_urls:
                    continue

                text = link.text.strip()
                container_text = text
                try:
                    container = link.find_element(
                        By.XPATH,
                        "./ancestor::*[contains(@class, 'list-group-item')][1]",
                    )
                    container_text = container.text.strip() or text
                except Exception:
                    pass

                entries.append(
                    DownloadEntry(
                        href=href,
                        text=container_text,
                        note_date=self.extract_note_date(container_text),
                        download_key=self.extract_download_key(href),
                    )
                )
                seen_urls.add(href)

            next_button = None
            for by, selector in NEXT_PAGE_SELECTORS:
                elements = self.driver.find_elements(by, selector)
                if elements:
                    candidate = elements[0]
                    classes = candidate.get_attribute("class") or ""
                    aria_disabled = candidate.get_attribute("aria-disabled") or ""
                    if "disabled" not in classes.lower() and aria_disabled.lower() != "true":
                        next_button = candidate
                        break

            if not next_button:
                break

            first_link = self.driver.find_elements(By.XPATH, DOWNLOAD_LINK_XPATH)
            marker = first_link[0] if first_link else next_button
            next_button.click()

            try:
                WebDriverWait(self.driver, self.settings.wait_timeout).until(EC.staleness_of(marker))
            except TimeoutException:
                time.sleep(2)

        return entries
