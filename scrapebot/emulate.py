import sys
import enum
import datetime
import json
import time
import random
import platform
import traceback
from pyvirtualdisplay import Display
# https://selenium-python.readthedocs.io
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


class RecipeStepTypeEnum(enum.Enum):
    navigate = '-> Navigate to the URL as provided in "value"'

    find_by_id = '| Find an element using its ID as provided in "value"'
    find_by_name = '| Find an element using its name as provided in "value"'
    find_by_class = '| Find one or many element(s) using a CSS class name as provided in "value"'
    find_by_tag = '| Find one or many element(s) using a tag name as provided in "value"'
    find_by_link = '| Find one or many <a> element(s) by searching for their complete link as provided in "value"'
    find_by_link_partial = '| Find one or many <a> element(s) by searching for parts of their link as provided in ' \
                           '"value"'
    find_by_css = '| Find one or many element(s) using a more sophisticated CSS selector as provided in "value"'
    find_by_xpath = '| Find one or many element(s) using a more sophisticated XPath selector as provided in "value"'

    random_select = '| Randomly select one element of the ones that have been identified in the previous step'

    scroll_to = '| Scroll the page for "value" pixels (or the page bottom, if not specified) with random breaks'
    pause = '| Wait for value seconds (+/- 25% to introduce some randomness)'
    click = '-> Click on the element which has been identified in the previous step'
    write = '. Write "value" onto the element which has been identified in the previous step'
    write_slowly = '. Write "value" slowly (i.e., character by character, pausing in between, like slow typing) ' \
                   'onto the the element which has been identified in the previous step'
    submit = '-> Submit on the element which has been identified in the previous step'

    get_text = '<- Store the text of the first element which has been identified in the previous step as data'
    get_texts = '<<- Store all texts of all elements identified in the previous step as data'
    get_value = '<- Store the value of the first element which has been identified in the previous step as data'
    get_values = '<<- Store all values of all elements identified in the previous step as data'
    get_attribute = '<- Store the value of the attribute as provided in "value" of the first element which has been ' \
                    'identified in the previous step as data'
    get_attributes = '<<- Store the values of the attributes as provided in "value" of all elements which have been ' \
                     'identified in the previous step as data'
    get_pagetitle = '<- Store the page title as data'
    get_element_count = '<- Store the number of previously found elements as data'
    get_htmlsource = '<- Store the complete HTML source code (WARNING: huuuge amount of data; handle with great care)'

    log = '. Simply log "value" into the log file'
    data = '. Store "value" as data entry'
    execute_js = '. Execute "value" as JavaScript code (store any returned value as data)'
    go_back = '<- Go back one step in the browser history'
    go_forward = '-> Go forward one step in the browser history (only available if you went back before)'
    unset_prior_element = '. Remove any previously retrieved element (which could cause error upon further navigation)'
    screenshot = '. Take a screenshot of the whole page as PNG file'
    sometimes_screenshot = '. Only take a screenshot of the whole page in 5% of the runs of this recipe on any instance'
    element_screenshot = '. Take a screenshot of the element which has been identified in the previous step as PNG file'

    # @todo?: allow steps to be grouped (through parent steps) and randomly chosen (either one step or random order)

    @classmethod
    def choices(cls):
        return [(choice.name, choice.value) for choice in cls]

    @classmethod
    def coerce(cls, item):
        try:
            return item.name if isinstance(item, RecipeStepTypeEnum) else item
        except KeyError:
            return None


class Emulator:
    __selenium = None
    __display = None
    __timeout = 0
    __config = None

    def run(self, config, run, step, prior_step=None):
        from scrapebot.database import Log, RunStatusEnum
        if prior_step is None:
            self.__config = config
            if not self.__init_browser(run):
                return RunStatusEnum.error
        else:
            if self.__timeout > 0:
                timeout = random.uniform(self.__timeout*.75, self.__timeout*1.25)
                run.log.append(Log(message='Waiting for ' + str(round(timeout, 1)) + ' seconds'))
                time.sleep(timeout)
        return self.__handle(run, step, prior_step)

    def __init_browser(self, run):
        from scrapebot.database import Log, LogTypeEnum
        browser = self.__config.get('Instance', 'browser', fallback='Firefox')
        executable = self.__config.get('Instance', 'BrowserBinary', fallback='')
        user_agent = self.__config.get('Instance', 'BrowserUserAgent', fallback='')
        language = self.__config.get('Instance', 'BrowserLanguage', fallback='en')
        try:
            lib_prefix = self.__config.get('Instance', 'LibDirPrefix', fallback='')
            browser_width = int(self.__config.get('Instance', 'BrowserWidth', fallback=1024))
            browser_height = int(self.__config.get('Instance', 'BrowserHeight', fallback=768))
            display_width = int(browser_width*1.2)
            display_height = int(browser_height*1.2)
            if platform.system() == 'Linux':
                self.__display = Display(visible=0, size=(display_width, display_height))
                self.__display.start()
                run.log.append(Log(message='Running on a virtual display at ' + str(display_width) + ' by ' +
                                           str(display_height)))
            if browser == 'Firefox':
                gecko = '32' if platform.architecture()[0].startswith('32') else '64'
                if platform.system() == 'Linux':
                    if platform.machine().lower().startswith('arm'):
                        gecko = lib_prefix + 'lib/geckodriver-arm-v0.23'
                    else:
                        gecko = lib_prefix + 'lib/geckodriver-linux' + gecko
                elif platform.system() == 'Darwin':
                    gecko = lib_prefix + 'lib/geckodriver-macos'
                else:
                    gecko = lib_prefix + 'lib/geckodriver-win' + gecko + '.exe'
                profile = webdriver.FirefoxProfile()
                if user_agent != '':
                    profile.set_preference('general.useragent.override', user_agent)
                profile.set_preference('intl.accept_languages', language)
                run.log.append(Log(message='Browser accept language set to "' + language + '"'))
                if executable == '':
                    self.__selenium = webdriver.Firefox(firefox_profile=profile, executable_path=gecko)
                    run.log.append(Log(message='Browser instance set to Firefox with Geckodriver "' + gecko + '"'))
                else:
                    self.__selenium = webdriver.Firefox(firefox_profile=profile,
                                                        executable_path=gecko,
                                                        firefox_binary=FirefoxBinary(executable))
                    run.log.append(Log(message='Browser instance set to Firefox with Geckodriver "' + gecko +
                                               '" and executable path "' + executable + '"'))
            elif browser == 'Chrome':
                if executable == '':
                    if platform.system() == 'Linux':
                        if platform.machine().lower().startswith('arm'):
                            executable = lib_prefix + 'lib/chromedriver-arm'
                        else:
                            executable = lib_prefix + 'lib/chromedriver-linux'
                    elif platform.system() == 'Darwin':
                        executable = lib_prefix + 'lib/chromedriver-macos'
                    else:
                        executable = lib_prefix + 'lib/chromedriver-win.exe'
                options = webdriver.ChromeOptions()
                if user_agent != '':
                    options.add_argument('--user-agent=' + user_agent)
                options.add_argument('--lang=' + language)
                options.add_experimental_option('prefs', {'intl.accept_languages': language})
                run.log.append(Log(message='Browser accept language set to "' + language + '"'))
                self.__selenium = webdriver.Chrome(executable_path=executable, chrome_options=options)
                run.log.append(Log(message='Browser instance set to Chrome with ChromeDriver "' + executable + '"'))
            else:
                webdriver_class = getattr(webdriver, browser)
                if executable == '':
                    self.__selenium = webdriver_class()
                    run.log.append(Log(message='Browser instance set to ' + browser))
                else:
                    self.__selenium = webdriver.Chrome(executable_path=executable)
                    run.log.append(Log(message='Browser instance set to ' + browser + ' with executable path "' +
                                               executable + '"'))
            self.__selenium.set_window_size(browser_width, browser_height)
            run.log.append(Log(message='Browser size set to ' + str(browser_width) + ' by ' +
                                       str(browser_height) + ' pixel'))
            self.__timeout = float(self.__config.get('Instance', 'Timeout', fallback=0))
            run.log.append(Log(message='Browser timeout set to ' + str(self.__timeout) + ' seconds'))
            user_agent = self.__selenium.execute_script('return navigator.userAgent')
            run.log.append(Log(message='User agent for this session is "' + user_agent + '"'))
            # @todo?: add encoding (Accept-Charset and Accept); however, neither is currently available to Selenium
            return True
        except WebDriverException:
            if sys.exc_info()[2] is not None:
                run.log.append(Log(message=browser + ' has raised the following error: ' + traceback.format_exc(),
                                   type=LogTypeEnum.error))
            else:
                run.log.append(Log(message='Browser instance "' + browser + '" not found', type=LogTypeEnum.error))
            self.close_session(run)
            return False
        except:
            if sys.exc_info()[2] is not None:
                run.log.append(Log(message=traceback.format_exc(), type=LogTypeEnum.error))
            self.close_session(run)
            return False

    def close_session(self, run):
        from scrapebot.database import Log
        if self.__selenium is not None:
            if run.recipe.cookies:
                order = run.get_recipe_order()
                if order is not None:
                    order.cookies_from_last_run = json.dumps(self.__selenium.get_cookies())
                    run.log.append(Log(message='Cookies stored'))
            self.__selenium.quit()
            run.log.append(Log(message='Browser session closed'))
        if self.__display is not None:
            try:
                self.__display.stop()
                run.log.append(Log(message='Virtual display closed'))
            except:
                return False

    def __get_first_elem_or_none(self, element):
        if element is None:
            return None
        elif isinstance(element, list):
            return element[0] if len(element) > 0 else None
        else:
            return element

    def __get_elem_list(self, elements):
        if elements is None:
            return []
        elif isinstance(elements, list):
            return elements
        else:
            return [elements]

    def __handle(self, run, step, prior_step=None):
        from scrapebot.database import Log, LogTypeEnum, RunStatusEnum, Data
        if step.type.name == 'log':
            run.log.append(Log(message=step.value))
        elif step.type.name == 'data':
            run.data.append(Data(step=step, value=step.value))
        elif step.type.name == 'execute_js':
            return_value = self.__selenium.execute_script(step.value)
            if return_value:
                run.data.append(Data(step=step, value=return_value))
                run.log.append(Log(message='Ran some JavaScript code, return values stored as data'))
            else:
                run.log.append(Log(message='Ran JavaScript code, no return values retrieved'))
        elif step.type.name == 'navigate':
            self.__selenium.get(step.value)
            if run.recipe.cookies:
                order = run.get_recipe_order()
                if order is not None:
                    cookies = json.loads(order.cookies_from_last_run)
                    for cookie in cookies:
                        self.__selenium.add_cookie(cookie)
                    run.log.append(Log(message='Cookies loaded for browser session'))
                    self.__selenium.get(step.value)
            run.log.append(Log(message='Navigated to "' + step.value + '"'))
        elif step.type.name == 'click':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available for clicking', type=LogTypeEnum.warning))
            else:
                element.click()
                run.log.append(Log(message='Clicked on previously retrieved element'))
        elif step.type.name == 'submit':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available for submitting', type=LogTypeEnum.warning))
            else:
                element.submit()
                run.log.append(Log(message='Submitted on previously retrieved element'))
                prior_step.temp_result = None
                step.temp_result = None
                run.log.append(Log(message='Removed previously retrieved element as it may disappear after submit'))
        elif step.type.name == 'pause':
            pause = int(step.value)
            pause = random.uniform(pause*.75, pause*1.25)
            time.sleep(pause)
            run.log.append(Log(message='Paused for ' + str(round(pause, 1)) + ' seconds'))
        elif step.type.name == 'write':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available for typing', type=LogTypeEnum.warning))
            else:
                element.send_keys(step.value)
                run.log.append(Log(message='Typed "' + step.value + '" on previously retrieved element'))
        elif step.type.name == 'write_slowly':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available for typing', type=LogTypeEnum.warning))
            else:
                for char in step.value:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.1, 1))
                run.log.append(Log(message='Typed "' + step.value + '" very slowly on previously retrieved element'))
        elif step.type.name == 'scroll_to':
            scroll_to = -1
            try:
                scroll_to = int(step.value)
                if scroll_to == 0:
                    raise ValueError
                run.log.append(Log(message='Scrolling for ' + str(scroll_to) + ' pixels'))
            except ValueError:
                scroll_to = -1
                run.log.append(Log(message='Scrolling to the bottom of the page'))
            scroll_step = 10 if scroll_to > 10 or scroll_to == -1 else scroll_to
            scroll_js = 'function scroll_and_wait(step, scrolled, last_pos, limit) {' \
                'if(window.pageYOffset > last_pos && (scrolled <= limit || limit < 0)) {' + \
                'last_pos = window.pageYOffset;' + \
                'window.scrollBy(0, step);' + \
                'setTimeout(scroll_and_wait, 20, step, (scrolled+step), last_pos, limit);' + \
                '}' + \
                '}' + \
                'scroll_and_wait(' + str(scroll_step) + ', 0, -1, ' + str(scroll_to) + ')'
            self.__selenium.execute_script(scroll_js)
        elif step.type.name == 'go_back':
            self.__selenium.back()
            run.log.append(Log(message='Navigated back one page'))
        elif step.type.name == 'go_forward':
            self.__selenium.forward()
            run.log.append(Log(message='Navigated forward one page'))
        elif step.type.name == 'screenshot' or step.type.name == 'sometimes_screenshot':
            screenshot = True
            if step.type.name == 'sometimes_screenshot':
                latest_runs = run.recipe.get_latest_runs(20, run.instance)
                for late_run in latest_runs:
                    if screenshot:
                        for single_data in late_run.data:
                            if single_data.step is step and single_data.value is not '':
                                screenshot = False
                                run.log.append(Log(message='No screenshot taken this time'))
                                break
            if screenshot:
                # Selenium cannot take full-size screenshots, so here's a little workaround
                # @see https://stackoverflow.com/a/52572919
                original_size = self.__selenium.get_window_size()
                required_width = self.__selenium.execute_script('return document.body.parentNode.scrollWidth')
                required_height = self.__selenium.execute_script('return document.body.parentNode.scrollHeight')
                self.__selenium.set_window_size(required_width, required_height)
                screenshot_name = self.__store_screenshot(self.__selenium.find_element_by_tag_name('body'), run, step)
                self.__selenium.set_window_size(original_size['width'], original_size['height'])
                run.log.append(Log(message='Screenshot stored as ' + screenshot_name + ' and referenced as data'))
        elif step.type.name == 'element_screenshot':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available to screenshot', type=LogTypeEnum.warning))
            else:
                screenshot_name = self.__store_screenshot(element, run, step)
                run.log.append(Log(message='Element screenshot stored as ' + screenshot_name +
                                           ' and referenced as data'))
        elif step.type.name == 'find_by_id':
            try:
                step.temp_result = self.__selenium.find_element_by_id(step.value)
                run.data.append(Data(step=step, value='1'))
                run.log.append(Log(message='Element with ID "' + step.value + '" retrieved (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='Element with ID "' + step.value + '" not found (stored 0 as data)',
                                   type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_name':
            try:
                step.temp_result = self.__selenium.find_element_by_name(step.value)
                run.data.append(Data(step=step, value='1'))
                run.log.append(Log(message='Element with name "' + step.value + '" retrieved (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No element with name "' + step.value + '" found (stored 0 as data)',
                                   type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_class':
            try:
                step.temp_result = self.__selenium.find_elements_by_class_name(step.value)
                count = str(len(step.temp_result))
                run.data.append(Data(step=step, value=count))
                run.log.append(Log(message='Retrieved ' + count + ' element(s) with class "' + step.value +
                                           '" (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No element with class "' + step.value + '" found (stored 0 as data)',
                                   type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_tag':
            try:
                step.temp_result = self.__selenium.find_elements_by_tag_name(step.value)
                count = str(len(step.temp_result))
                run.data.append(Data(step=step, value=count))
                run.log.append(Log(message='Retrieved ' + count + ' "' + step.value + '" element(s) '
                                                                                      '(count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No "' + step.value + '" element found (stored 0 as data)',
                                   type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_link':
            try:
                step.temp_result = self.__selenium.find_elements_by_link_text(step.value)
                count = str(len(step.temp_result))
                run.data.append(Data(step=step, value=count))
                run.log.append(Log(message='Retrieved ' + count + ' element(s) with link "' + step.value +
                                           '" (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No element with link "' + step.value + '" found (stored 0 as data)',
                                   type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_link_partial':
            try:
                step.temp_result = self.__selenium.find_elements_by_partial_link_text(step.value)
                count = str(len(step.temp_result))
                run.data.append(Data(step=step, value=count))
                run.log.append(Log(message='Retrieved ' + count + ' element(s) with link partially equal to "' +
                                           step.value + '" (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No element with link containing "' + step.value +
                                           '" found (stored 0 as data)', type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_css':
            try:
                step.temp_result = self.__selenium.find_elements_by_css_selector(step.value)
                count = str(len(step.temp_result))
                run.data.append(Data(step=step, value=count))
                run.log.append(Log(message='Retrieved ' + count + ' element(s) with CSS selector "' + step.value +
                                           '" (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No element matching CSS selector "' + step.value +
                                           '" found (stored 0 as data)', type=LogTypeEnum.warning))
        elif step.type.name == 'find_by_xpath':
            try:
                step.temp_result = self.__selenium.find_elements_by_xpath(step.value)
                count = str(len(step.temp_result))
                run.data.append(Data(step=step, value=count))
                run.log.append(Log(message='Retrieved ' + count + ' element(s) with XPath "' + step.value +
                                           '" (count stored as data)'))
            except NoSuchElementException:
                step.temp_result = None
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No element from XPath "' + step.value + '" found (stored 0 as data)',
                                   type=LogTypeEnum.warning))
        elif step.type.name == 'random_select':
            if prior_step.temp_result is None:
                run.log.append(Log(message='No element from previous step found, hence no element randomly selected',
                                   type=LogTypeEnum.warning))
            elif isinstance(prior_step.temp_result, list):
                count = len(prior_step.temp_result)
                if count > 0:
                    i = random.randint(0, count-1)
                    step.temp_result = prior_step.temp_result[i]
                    run.data.append(Data(step=step, value=(i+1)))
                    run.log.append(Log(message='Randomly selected element ' + str(i+1) + '/' + str(count) +
                                               ' (stored ' + str(i+1) + ' as data)'))
                else:
                    run.log.append(
                        Log(message='No element from previous step found, hence no element randomly selected',
                            type=LogTypeEnum.warning)
                    )
            else:
                step.temp_result = prior_step.temp_result
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='Only one element from previous step found, so this was selected "randomly"'))
        elif step.type.name == 'get_text':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available to get text from', type=LogTypeEnum.warning))
            else:
                value = element.text
                run.data.append(Data(step=step, value=value))
                run.log.append(Log(message='Retrieved and stored text "' + value[:15] + '..." of prior element'))
        elif step.type.name == 'get_texts':
            elements = self.__get_elem_list(prior_step.temp_result)
            for element in elements:
                run.data.append(Data(step=step, value=element.text))
            run.log.append(Log(message='Stored text from ' + str(len(elements)) + ' element(s), each as separate data'))
        elif step.type.name == 'get_value':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available to get a value from', type=LogTypeEnum.warning))
            else:
                value = str(element.get_attribute('value'))
                run.data.append(Data(step=step, value=value))
                run.log.append(Log(message='Retrieved and stored value "' + value[:15] + '..." of prior element'))
        elif step.type.name == 'get_values':
            elements = self.__get_elem_list(prior_step.temp_result)
            for element in elements:
                run.data.append(Data(step=step, value=str(element.get_attribute('value'))))
            run.log.append(Log(message='Stored values from ' + str(len(elements)) +
                                       ' element(s), each as separate data'))
        elif step.type.name == 'get_attribute':
            element = self.__get_first_elem_or_none(prior_step.temp_result)
            if element is None:
                run.log.append(Log(message='No element available to get the attribute "' + step.value +
                                           '" from', type=LogTypeEnum.warning))
            else:
                value = str(element.get_attribute(step.value))
                run.data.append(Data(step=step, value=value))
                run.log.append(Log(message='Retrieved and stored value "' + value[:15] + '..." of attribute "' +
                                           step.value + '" of prior element'))
        elif step.type.name == 'get_attributes':
            elements = self.__get_elem_list(prior_step.temp_result)
            for element in elements:
                run.data.append(Data(step=step, value=str(element.get_attribute(step.value))))
            run.log.append(Log(message='Stored "' + step.value + '" values from ' + str(len(elements)) +
                                       ' element(s), each as separate data'))
        elif step.type.name == 'get_element_count':
            if prior_step.temp_result is None:
                run.data.append(Data(step=step, value='0'))
                run.log.append(Log(message='No previously retrieved elements found, thus stored "0"'))
            elif isinstance(prior_step.temp_result, list):
                value = str(len(prior_step.temp_result))
                run.data.append(Data(step=step, value=value))
                run.log.append(Log(message='Counted and stored ' + value + ' element(s)'))
            else:
                run.data.append(Data(step=step, value='1'))
                run.log.append(Log(message='Counted and stored only 1 element'))
        elif step.type.name == 'get_pagetitle':
            value = self.__selenium.title
            run.data.append(Data(step=step, value=value))
            run.log.append(Log(message='Retrieved and stored page title "' + value + '"'))
        elif step.type.name == 'get_htmlsource':
            value = self.__selenium.execute_script('return typeof(XMLSerializer) === \'undefined\' ? ' +
                                                   'document.body.parentElement.innerHTML : ' +
                                                   'new XMLSerializer().serializeToString(document)')
            run.data.append(Data(step=step, value=value))
            run.log.append(Log(message='Retrieved and stored HTML source code'))
        elif step.type.name == 'unset_prior_element':
            if step.temp_result is not None:
                prior_step.temp_result = None
                step.temp_result = None
                run.log.append(Log(message='Previously retrieved element removed'))
        else:
            return RunStatusEnum.config_error
        return RunStatusEnum.success

    def __store_screenshot(self, selenium_element, run, step):
        from scrapebot.database import Data
        png = selenium_element.screenshot_as_png
        screenshot_dir = self.__config.get('Instance', 'ScreenshotDirectory')
        screenshot_name = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.png'
        screenshot_log = ''
        if screenshot_dir is not None:
            if not screenshot_dir.endswith('/'):
                screenshot_dir = screenshot_dir + '/'
            local_file = open(screenshot_dir + screenshot_name, 'wb')
            local_file.write(bytearray(png))
            local_file.close()
            screenshot_log = screenshot_dir + screenshot_name
            run.data.append(Data(step=step, value=screenshot_log))
        if self.__config.get('Database', 'AWSaccess') is not None and \
           self.__config.get('Database', 'AWSsecret') is not None and \
           self.__config.get('Database', 'AWSbucket') is not None:
            import boto3
            client = boto3.client(
                's3',
                aws_access_key_id=self.__config.get('Database', 'AWSaccess'),
                aws_secret_access_key=self.__config.get('Database', 'AWSsecret')
            )
            s3_file = client.put_object(
                Bucket=self.__config.get('Database', 'AWSbucket'),
                Key=screenshot_name,
                Body=png,
                Metadata={
                    'Instance': run.instance.name,
                    'Run': str(run.uid),
                    'Step': str(step.uid)
                }
            )
            screenshot_name = 's3://' + self.__config.get('Database', 'AWSbucket') + '/' + screenshot_name
            if screenshot_log is '':
                screenshot_log = screenshot_name
            else:
                screenshot_log = screenshot_log + ' and ' + screenshot_name
            run.data.append(Data(step=step, value=screenshot_name))
        return screenshot_log
