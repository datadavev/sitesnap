"""
Quickie for evaluating load performance of search.dataone.org

Uses Selenium, https://selenium-python.readthedocs.io

"""
import sys
import argparse
import logging
import time
import json
import selenium.common.exceptions
from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pprint import pprint

def pageHasLoaded(driver):
    logging.debug("Checking if {} page is loaded.".format(driver.current_url))
    page_state = driver.execute_script('return document.readyState;')
    return page_state == 'complete'

def ajaxNotActive(driver):
    jquery_state = False
    try:
        jquery_state = driver.execute_script("return $.active == 0")
    except selenium.common.exceptions.WebDriverException:
        jquery_state = False
    return jquery_state


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l",
        "--log_level",
        action="count",
        default=0,
        help="Set logging level, multiples for more detailed.",
    )
    parser.add_argument("url", default=None, help="URL to retrieve")
    args = parser.parse_args()
    # Setup logging verbosity
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(len(levels) - 1, args.log_level)]
    logging.basicConfig(level=level)
    if args.url is None:
        logging.warning("No URL provided.")
        return 1
    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}
    caps["headless"] = True

    driver = webdriver.Chrome("chromedriver", desired_capabilities=caps)
    logging.info("Starting access to %s", args.url)
    tstart = time.time()
    driver.get(args.url)
    wait = ui.WebDriverWait(driver, 6)
    done = False
    elapsed = 0
    tdisp = 0
    logging.info("Waiting for readyState")
    wait.until(lambda driver: pageHasLoaded(driver))
    logging.info("Waiting for element...")
    wait.until(lambda driver: driver.find_element_by_class_name("metadata-view"))
    logging.info("Waiting for stuff to load...")
    while not done:
        if ajaxNotActive(driver):
            done = True
        else:
            elapsed = time.time() - tstart
            time.sleep(0.1)
            if int(elapsed) % 1 == 0 and int(elapsed) != tdisp:
                logging.info("Elapsed = %.2f" % elapsed)
                tdisp = int(elapsed)
            if elapsed > 60:
                logging.error("Been waiting more than a minute. Bailing...")
                done = True
    tend = time.time()
    logging.info("End access to %s", args.url)
    print(f"Elapsed time {tend - tstart}")
    for entry in driver.get_log('performance'):
        msg = json.loads(entry["message"])
        #pprint(msg)
        if msg["message"]["method"] == "Network.requestWillBeSent":
            #print(msg["message"]["params"]["documentURL"])
            #pprint(msg["message"]["params"], indent=2)
            #print(msg["message"]["params"]["request"]["url"])
            pass
        if msg["message"]["method"] == "Network.responseReceived":
            # Timing info: https://chromedevtools.github.io/devtools-protocol/tot/Network#type-ResourceTiming
            r = msg["message"]["params"]["response"]
            cstart = r["timing"]["connectStart"]
            ctime = r["timing"]["connectEnd"] - cstart
            duration = r["timing"]["receiveHeadersEnd"] - cstart
            print(f"{r['timing']['requestTime']} {ctime} {duration} {r['status']} {r['url']} ")
    driver.close()

if __name__ == "__main__":
    sys.exit(main())