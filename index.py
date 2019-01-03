'''
imports reading list from mangaupdates.com to mangadex.org

requires:
beautifulsoup4
chromedriver-binary (to be installed in python3 directory)
PyYAML
selenium

./credentials.yaml

mu_username: <account name>
mu_password: <password>
md_username:<account name>
md_password: <password>
'''
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import yaml


# constants
# delays
MANGA_UPDATES_DELAY = 0  # seconds for manga updates to load, usually can be set to 0
MANGADEX_DELAY = 2  # seconds for mangadex to load (jQuery takes forever)
# overwrite all progress on mangadex for manga update's progress
# make sure you really want this changed
OVERWRITE_PROGRESS = False

# urls
mu_url = 'https://www.mangaupdates.com/mylist.html'
mu_url_wish_list = 'https://www.mangaupdates.com/mylist.html?list=wish'
mu_url_complete_list = 'https://www.mangaupdates.com/mylist.html?list=complete'
mu_url_unfinished_list = 'https://www.mangaupdates.com/mylist.html?list=unfinished'
mu_url_on_hold_list = 'https://www.mangaupdates.com/mylist.html?list=hold'
md_base_url = 'https://mangadex.org'
md_login_url = 'https://mangadex.org/login'
md_search_url = 'https://mangadex.org/quick_search/'


def manga_updates_list(driver, url=mu_url):
    '''
    gets list's unique urls and titles
    '''
    driver.get(url)
    # parse urls and titles of list
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    reading_list = soup.find("table", {"id": "list_table"})
    title_url_list = reading_list.find_all("a", {"title": "Series Info"})
    href_list = [a.get("href") for a in title_url_list]
    # main title is not featured in associated names
    title_list = [u.get_text() for u in title_url_list]

    return href_list, title_list


def manga_updates_reading_progress(driver, reading_list):
    '''
    gets reading list and returns dict of url: (volume number, chapter number)
    '''

    reading_progress = dict()

    for url in reading_list.keys():
        driver.get(url)
        time.sleep(MANGA_UPDATES_DELAY)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        volume, chapter = soup.find("td", {"id": "showList"}).find_all("b")
        volume = "".join([x for x in list(list(volume)[0]) if x.isdigit()])
        chapter = "".join([x for x in list(list(chapter)[0]) if x.isdigit()])
        reading_progress[url] = (int(volume), int(chapter))

    return reading_progress


def manga_updates_all_titles(driver, url=mu_url):
    '''
    get a list of titles and returns a dict of manga_updates_url: set(all titles)
    '''
    all_titles = {}

    href_list, title_list = manga_updates_list(driver, url)

    # initially fill with known values
    for i in range(len(title_list)):
        new_title_set = set()
        new_title_set.add(title_list[i])
        all_titles[href_list[i]] = new_title_set

    # scrape each individual page for alternative titles
    for manga_urls in href_list:
        driver.get(manga_urls)
        time.sleep(MANGA_UPDATES_DELAY)

        # alternate titles are under first sContainer, third sContent
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        title_html = soup.find_all("div", {"class": "sContent"})[3]
        title_list = title_html.find_all(text=True)
        title_list = [title.strip(' \t\n\r')
                      for title in title_list if title != '\n']
        all_titles[manga_urls].update(title_list)

        return all_titles


def is_english(s):
    '''
    tests to see if the characters are english
    MangaDex does not have non-english characters titles
    '''
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def mangadex_import(all_titles, driver, type="reading"):
    '''
    imports to correct list base on an all_titles dict
    all_titles: manga_updates_url: set(titles)
    '''

    x_path_string = ""

    if type == "reading":
        x_path_string = "//a[contains(@class, 'manga_follow_button') and contains(@id, '1')]"
    elif type == "completed":
        x_path_string = "//a[contains(@class, 'manga_follow_button') and contains(@class, 'dropdown-item') and contains(@id, '2')]"
    elif type == "on hold":
        x_path_string = "//a[contains(@class, 'manga_follow_button') and contains(@class, 'dropdown-item') and contains(@id, '3')]"
    elif type == "plan to read":
        x_path_string = "//a[contains(@class, 'manga_follow_button') and contains(@class, 'dropdown-item') and contains(@id, '4')]"
    elif type == "dropped":
        x_path_string = "//a[contains(@class, 'manga_follow_button') and contains(@class, 'dropdown-item') and contains(@id, '5')]"
    else:
        raise Exception(
            "import type should be: 'reading', 'completed', 'on hold', 'plan to read', 'dropped'")

    # start searching
    for titles in all_titles.values():
        for title_name in titles:
            if not is_english(title_name):
                continue
            query = title_name.replace(" ", "%20")
            driver.get(md_search_url+query)
            time.sleep(MANGADEX_DELAY)  # wait for jQuery to load
            try:
                manga_entries = driver.find_elements_by_class_name(
                    "manga-entry")
                if manga_entries:
                    try:
                        manga_entries[0].find_element_by_xpath(
                            "//button[contains(@class, 'btn-secondary') and contains(@class, 'dropdown-toggle')]").click()
                        manga_entries[0].find_elements_by_xpath(x_path_string)[
                            0].click()

                    except:
                        print("already imported:", title_name)
                        pass
                    break  # a valid title has been found
            except:
                pass


def mangadex_import_progress(all_titles, driver, progress):
    '''
    imports chapter and volume information for items in reading list
    '''
    for key, titles in all_titles.items():
        for title_name in titles:
            if not is_english(title_name):
                continue
            query = title_name.replace(" ", "%20")
            driver.get(md_search_url+query)
            time.sleep(MANGADEX_DELAY)  # wait for jQuery to load
            try:
                manga_entries = driver.find_elements_by_class_name(
                    "manga-entry")
                if manga_entries:
                    try:
                        driver.find_elements_by_class_name(
                            "manga-entry")[0].find_element_by_class_name(
                            "manga_title").click()

                        time.sleep(MANGADEX_DELAY)

                        # edit menu
                        volume, chapter = progress[key]
                        driver.find_element_by_id("edit_progress").click()

                        # find inputs
                        vol_input = driver.find_element_by_id("volume")
                        ch_input = driver.find_element_by_id("chapter")

                        # input new value
                        driver.execute_script(
                            "arguments[0].setAttribute('value', arguments[1])", vol_input, volume)
                        driver.execute_script(
                            "arguments[0].setAttribute('value', arguments[1])", ch_input, chapter)

                        # submit
                        driver.find_element_by_id(
                            "edit_progress_button").click()

                    except:
                        print("overwrite progress import error occurred")
                        pass
                    break  # a valid title has been found
            except:
                pass


def main():
    # get credentials
    credentials = {}
    with open('credentials.yaml') as f:
        credentials = yaml.load(f)

    # set driver options
    options = webdriver.chrome.options.Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    driver = webdriver.Chrome(options=options)
    driver.get(mu_url)
    time.sleep(MANGA_UPDATES_DELAY)

    # manga updates authenticate
    username = driver.find_element_by_xpath("//input[@name='username']")
    password = driver.find_element_by_xpath("//input[@name='password']")
    submit = driver.find_element_by_xpath("//input[@src='images/login.gif']")

    username.send_keys(credentials['mu_username'])
    password.send_keys(credentials['mu_password'])
    submit.click()
    time.sleep(MANGA_UPDATES_DELAY)

    # get lists
    reading_list = manga_updates_all_titles(driver, mu_url)
    wish_list = manga_updates_all_titles(driver, mu_url_wish_list)
    complete_list = manga_updates_all_titles(driver, mu_url_complete_list)
    unfinished_list = manga_updates_all_titles(driver, mu_url_unfinished_list)
    on_hold_list = manga_updates_all_titles(driver, mu_url_on_hold_list)

    reading_list_progress = manga_updates_reading_progress(
        driver, reading_list)

    # login to mangadex
    driver.get(md_login_url)
    time.sleep(MANGADEX_DELAY)

    username = driver.find_element_by_id("login_username")
    password = driver.find_element_by_id("login_password")
    submit = driver.find_element_by_id("login_button")

    username.send_keys(credentials['md_username'])
    password.send_keys(credentials['md_password'])
    submit.click()

    # mangadex can be slow sometimes
    time.sleep(MANGADEX_DELAY)

    # import to mangadex
    mangadex_import(reading_list, driver)
    mangadex_import(wish_list, driver, "plan to read")
    mangadex_import(complete_list, driver, "completed")
    mangadex_import(unfinished_list, driver, "dropped")
    mangadex_import(on_hold_list, driver, "on hold")

    # handle importing of chapters
    if OVERWRITE_PROGRESS:
        mangadex_import_progress(reading_list, driver, reading_list_progress)

    # exit selenium
    driver.quit()


if __name__ == "__main__":
    main()
