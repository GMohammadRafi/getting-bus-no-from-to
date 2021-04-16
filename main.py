import time
import os
from flask import Flask
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

app = Flask('__name__')

user_need_details = {}


def check_exists_by_selector(css_selector, driver):
    try:
        driver.find_element_by_css_selector(css_selector)
    except NoSuchElementException:
        return False
    return True


def get_url_setting_to_loc(from_loc_lat, from_loc_long, to_loc_lat, to_loc_long):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN") or "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH") or "chromedriver.exe", options=chrome_options)
    driver.get(f"https://www.google.com/maps/@{from_loc_lat},{from_loc_long},15z")
    try:
        driver.find_element_by_css_selector("#gs_lc50 input").send_keys(f"{to_loc_lat},{to_loc_long}")
        driver.find_element_by_css_selector(".searchbox-directions-container button").click()
        set_from_loc(from_loc_lat, from_loc_long, driver)
    except NoSuchElementException:
        driver.close()
        get_url_setting_to_loc(from_loc_lat, from_loc_long, to_loc_lat, to_loc_long)


def set_from_loc(from_loc_lat, from_loc_long, driver):
    try:
        time.sleep(1)
        driver.find_element_by_css_selector(".gstl_51 .sbib_b input").send_keys(f"{from_loc_lat},{from_loc_long}")
        driver.find_elements_by_css_selector(".adjusted-to-decreased-spacing div")[4].find_element_by_css_selector(
            "button").click()
        setting_bus_as_medium(driver)
    except NoSuchElementException:
        set_from_loc(from_loc_lat, from_loc_long, driver)


def setting_bus_as_medium(driver):
    try:
        time.sleep(1)
        driver.find_element_by_css_selector(".section-directions-trip-description button").click()
        get_user_details_from_website(driver)
    except NoSuchElementException:
        setting_bus_as_medium(driver)


def get_user_details_from_website(driver):
    time.sleep(1)
    temp = []

    def add_all(data, d):
        c = 0
        for i in range(len(data)):
            if data[i].text:
                temp[c][d] = data[i].text
                c += 1

    try:
        user_need_details["toatal_time"] = str(
            driver.find_element_by_css_selector(".section-layout-root .section-trip-summary h1").text)
        details = driver.find_element_by_css_selector(".section-layout-root .section-trip-details")
        locations = details.find_elements_by_css_selector(".transit-stop-details h2")
        bus_start_timings = details.find_elements_by_css_selector(
            ".transit-stop .directions-mode-group-departure-time")
        for i in range(len(bus_start_timings)):
            if bus_start_timings[i].text:
                temp.append({"starting_bus_timing": bus_start_timings[i].text})
        c = 0
        if len(locations) == len(temp) * 2:
            for i in range(0, len(locations), 2):
                temp[c]["starting_bus_stop"] = locations[i].text
                temp[c]["end_bus_stop"] = locations[i + 1].text
                c += 1
        else:
            for i in range(0, len(locations) - 1):
                temp[i]["starting_bus_stop"] = locations[i].text
                temp[i]["end_bus_stop"] = locations[i + 1].text
        # bus_end_timings = details.find_elements_by_css_selector(".transit-stop .directions-mode-group-arrival-time")
        # add_all(bus_end_timings, "ending_bus_timing")
        bus_no = details.find_elements_by_css_selector(".renderable-component-text-box-content")
        add_all(bus_no, "bus_no")
        timings_no_of_stop = details.find_elements_by_css_selector(".transit-step-details")
        c = 0
        for i in range(len(timings_no_of_stop)):
            if timings_no_of_stop[i].text and not str(timings_no_of_stop[i].text).startswith("About"):
                temp[c]["timings_and_no_of_stop"] = timings_no_of_stop[i].text
                c += 1
        user_need_details["bus_details"] = temp
        getting_iframe(driver)
    except NoSuchElementException:
        if check_exists_by_selector(".section-directions-trip-description button"):
            setting_bus_as_medium(driver)
        else:
            get_user_details_from_website(driver)


def getting_iframe(driver):
    def getting_iframe1():
        try:
            driver.find_elements_by_css_selector(".pa9YZC9ZNMi__section-directions-details-action button")[1].click()
        except:
            getting_iframe1()

    def getting_iframe2():
        try:
            driver.find_elements_by_css_selector(".section-tab-bar button")[1].click()
            user_need_details["iframe"] = \
                f'{driver.find_element_by_css_selector(".section-embed-map-controls input").get_attribute("value")}'
            return user_need_details
        except:
            getting_iframe2()

    time.sleep(1)
    getting_iframe1()
    getting_iframe2()
    driver.close()


@app.route('/<from_loc_lat>/<from_loc_long>/<to_loc_lat>/<to_loc_long>', methods=["GET"])
def get_bus_no_timings(from_loc_lat, from_loc_long, to_loc_lat, to_loc_long):
    try:
        get_url_setting_to_loc(from_loc_lat=from_loc_lat,
                               from_loc_long=from_loc_long,
                               to_loc_lat=to_loc_lat,
                               to_loc_long=to_loc_long
                               )
    except:
        return {
            "error": 300,
            "message": "Something went wrong"
        }
    while "iframe" not in user_need_details.keys():
        pass
    return user_need_details


@app.route('/', methods=["GET"])
def home():
    return {
        "Application": "My - BMTC"
    }


if __name__ == "__main__":
    if os.environ.get("GOOGLE_CHROME_BIN"):
        app.run()
    else:
        app.run(debug=True, host="192.168.0.100")
