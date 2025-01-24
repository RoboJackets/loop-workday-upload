"""
Upload data from Workday to Loop
"""

from argparse import ArgumentParser
from json import JSONDecodeError, dumps, loads
from typing import Any, Dict, Mapping

from requests import get, post, put

from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from seleniumwire import webdriver  # type: ignore
from seleniumwire.utils import decode  # type: ignore
from seleniumwire.webdriver import Chrome  # type: ignore

from webdriver_manager.chrome import ChromeDriverManager


def log_in_to_workday(driver: Chrome, username: str, password: str) -> None:
    """
    Log in to Workday via CAS
    """
    print("Starting Workday authentication")
    driver.get("https://wd5.myworkday.com/gatech/")

    # wait for CAS login page to load
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "username"))

    timeout = 20

    if username is not None and password is not None:
        # enter username, password, and submit the form
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.NAME, "submitbutton")

        print("Entering username")
        username_field.send_keys(username)
        print("Entering password")
        password_field.send_keys(password)
        print("Submitting login form")
        submit_button.click()
    else:
        timeout = 60

    # wait for Duo authentication to finish, redirect to Workday, and wait for Workday to start loading
    print("Waiting for authentication to complete")
    WebDriverWait(driver, timeout=timeout).until(lambda d: d.title == "Home - Workday")

    # Wait for the homepage to fully load, because if you don't, it'll close the search window later
    print("Waiting for homepage to fully load")
    (
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "div[data-automation-id='pex-home-banner']")
        )
    )


def search_for_expense_reports(driver: Chrome) -> str:  # pylint: disable=too-many-locals,too-many-statements
    """
    Retrieve all relevant expense reports
    """
    print("Navigating to expense report search")
    driver.get("https://wd5.myworkday.com/gatech/d/task/1422$269.htmld")

    # Wait for form to load
    print("Waiting for expense report search form to load")
    WebDriverWait(driver, timeout=20).until(lambda d: d.title == "Find Expense Reports by Organization - CR - Workday")

    # Enter Companies
    print("Entering Company")
    companies_field = driver.find_element(By.ID, "15$378585").find_element(By.TAG_NAME, "input")
    companies_field.send_keys("CO503 Georgia Institute of Technology" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-2501$1"))

    # Enter Student Life Cost Center
    print("Entering Student Life Cost Center")
    cost_center_field = driver.find_element(By.ID, "ExternalField146_7227PromptQualifier1").find_element(
        By.TAG_NAME, "input"
    )
    cost_center_field.send_keys("CC000375" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-2502$367"))

    print("Entering Mechanical Engineering Cost Center")
    cost_center_field = driver.find_element(By.ID, "ExternalField146_7227PromptQualifier1").find_element(
        By.TAG_NAME, "input"
    )
    cost_center_field.send_keys("CC000259" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-2502$180"))

    # Enter Work Tags
    print("Entering Custodial Entity worktag")
    work_tags_field = driver.find_element(By.ID, "ExternalField146_4946PromptQualifier1").find_element(
        By.TAG_NAME, "input"
    )
    work_tags_field.send_keys("CE0339" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-2506$9979"))
    print("Entering Designated Entity worktag")
    work_tags_field.send_keys("DE00007513" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-2506$38743"))
    print("Entering Gift account worktag")
    work_tags_field.send_keys("GTF250000211" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-8261$1948"))
    print("Entering Gift account worktag")
    work_tags_field.send_keys("GTF551000258" + Keys.ENTER)
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "pill-8261$7425"))
    print("Entering External Committee Member worktag")
    work_tags_field.send_keys("robojackets inc" + Keys.ENTER)
    WebDriverWait(driver, timeout=20).until(lambda d: d.find_element(By.ID, "menuItem-15341$7955"))
    driver.find_element(By.ID, "menuItem-15341$7955").click()
    WebDriverWait(driver, timeout=20).until(lambda d: d.find_element(By.ID, "pill-15341$7955"))
    print("Entering External Committee Member worktag")
    work_tags_field.send_keys("robo jackets" + Keys.ENTER)
    WebDriverWait(driver, timeout=20).until(lambda d: d.find_element(By.ID, "menuItem-15341$1787"))

    # Tab over to Report Date On or After
    print("Entering Report Date On or After")
    webdriver.ActionChains(driver).send_keys("".join([Keys.TAB] * 3)).perform()

    date_div = driver.find_element(By.ID, "ExternalField146_13403PromptQualifier2")

    date_inputs = date_div.find_elements(By.TAG_NAME, "input")

    year_input = None
    month_input = None
    day_input = None

    for date_input in date_inputs:
        if "Month" == date_input.get_attribute("aria-label"):
            month_input = date_input
        elif "Day" == date_input.get_attribute("aria-label"):
            day_input = date_input
        elif "Year" == date_input.get_attribute("aria-label"):
            year_input = date_input

    assert month_input is not None
    assert day_input is not None
    assert year_input is not None

    webdriver.ActionChains(driver).send_keys("01").perform()
    WebDriverWait(driver, timeout=10).until(lambda d: month_input.get_property("value") == "1")
    webdriver.ActionChains(driver).send_keys("01").perform()
    WebDriverWait(driver, timeout=10).until(lambda d: day_input.get_property("value") == "1")
    webdriver.ActionChains(driver).send_keys("2023").perform()
    WebDriverWait(driver, timeout=10).until(lambda d: year_input.get_property("value") == "2023")

    # Enter Payee Type
    print("Entering Payee Type")
    payee_type_field = driver.find_element(By.ID, "ExternalField3285_1140PromptQualifier1").find_element(
        By.TAG_NAME, "input"
    )
    payee_type_field.click()

    # Wait for dropdown to populate
    WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.ID, "menuItem-9572$14"))

    # Click External Committee Member
    external_committee_member_checkbox = driver.find_element(By.ID, "menuItem-9572$14")
    external_committee_member_checkbox.click()

    del driver.requests

    # Click OK
    print("Submitting form")
    driver.find_element(By.CSS_SELECTOR, "button[data-automation-id='wd-CommandButton_uic_okButton']").click()

    # Wait for results to load
    print("Waiting for report results to load")
    WebDriverWait(driver, timeout=30).until(
        lambda d: d.find_element(By.ID, "wd-PageContent-6$8105").find_element(
            By.XPATH, "//div[@title='Export to Excel']"
        )
    )

    chunking_url = None

    for request in driver.iter_requests():
        if request.url != "https://wd5.myworkday.com/gatech/flowController.htmld":
            continue

        response = request.response

        if response is None:
            continue

        if response.status_code != 200:
            continue

        try:
            widgets = loads(decode(response.body, response.headers.get("Content-Encoding", "identity")))

            if (
                "body" in widgets
                and "children" in widgets["body"]
                and len(widgets["body"]["children"]) > 2
                and "chunkingUrl" in widgets["body"]["children"][2]
            ):
                chunking_url = widgets["body"]["children"][2]["chunkingUrl"]
        except JSONDecodeError:
            print("Failed to decode JSON")

    if chunking_url is not None:
        print("Found chunking URL")
        return chunking_url  # type: ignore

    raise ValueError("Could not find chunkingUrl")


def search_for_key_value_pair(widgets: Any, key: str, value: str) -> list[Mapping[str, Any]]:
    """
    Search through Workday widgets to find one with a given key-value pair.
    """
    results = []

    if isinstance(widgets, Mapping) and key in widgets.keys() and widgets[key] == value:
        results.append(widgets)
    elif isinstance(widgets, Mapping):
        for item in widgets:
            results.extend(search_for_key_value_pair(widgets[item], key, value))
    elif isinstance(widgets, list):
        for item in widgets:
            results.extend(search_for_key_value_pair(item, key, value))

    return results


def sync_expense_report_line(  # pylint: disable=too-many-positional-arguments
    cookies: Dict[str, str], get_line_url: str, instance_id: str, line_id: str, server: str, token: str
) -> None:
    """
    Sync a single expense report line from Loop to Workday
    """
    print(f"Retrieving expense report line {line_id} for expense report {instance_id} from Workday")
    workday_response = post(
        url=f"https://wd5.myworkday.com{get_line_url}.htmld", cookies=cookies, data={"id": line_id}, timeout=(5, 5)
    )

    if workday_response.status_code != 200:
        print(workday_response.status_code)
        print(workday_response.text)
        raise ValueError("Unexpected response code from Workday")

    print(f"Uploading expense report line {line_id} for expense report {instance_id} to Loop")

    loop_response = put(
        url=f"{server}/api/v1/workday/expense-reports/{instance_id}/lines/{line_id}",
        json=workday_response.json(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=(5, 5),
    )

    if loop_response.status_code != 200:
        print(workday_response.text)
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")

    print(loop_response.status_code)
    print(loop_response.text)

    for attachment in loop_response.json()["attachments"]:
        print(f"Downloading attachment {attachment} from Workday")
        values = search_for_key_value_pair(workday_response.json(), "instanceId", f"1074${attachment}")

        if len(values) != 1:
            print(dumps(workday_response.json()))
            print(dumps(values))
            raise ValueError("Did not find exactly one widget")

        workday_attachment_response = get(
            url=f"https://wd5.myworkday.com/gatech/attachment/1074${attachment}/{values[0]['target']}.htmld",
            cookies=cookies,
            timeout=(5, 5),
        )

        if workday_attachment_response.status_code != 200:
            print(workday_attachment_response.status_code)
            print(workday_attachment_response.text)
            raise ValueError("Unexpected response code from Workday")

        print(f"Uploading attachment {attachment} to Loop")

        loop_attachment_response = post(
            url=f"{server}/api/v1/workday/expense-reports/{instance_id}/lines/{line_id}/attachments/{attachment}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            files={"attachment": (values[0]["text"], workday_attachment_response.content)},
            timeout=(5, 10),
        )

        if loop_attachment_response.status_code != 200:
            print(loop_attachment_response.status_code)
            print(loop_attachment_response.text)
            raise ValueError("Unexpected response code from Loop")


def sync_expense_report(cookies: Dict[str, str], instance_id: str, server: str, token: str) -> None:
    """
    Sync a single expense report from Workday to Loop
    """
    print(f"Retrieving expense report {instance_id} from Workday")
    workday_response = get(
        url=f"https://wd5.myworkday.com/gatech/inst/1$1356/1356${instance_id}.htmld",
        cookies=cookies,
        timeout=(5, 5),
    )

    if workday_response.status_code != 200:
        print(workday_response.status_code)
        print(workday_response.text)
        raise ValueError("Unexpected response code from Workday")

    print(f"Uploading expense report {instance_id} to Loop")

    loop_response = put(
        url=f"{server}/api/v1/workday/expense-reports/{instance_id}",
        json=workday_response.json(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=(5, 5),
    )

    if loop_response.status_code != 200:
        print(dumps(workday_response.json()))
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")

    values = search_for_key_value_pair(workday_response.json(), "widget", "extensionActions")

    if len(values) != 1:
        print(dumps(workday_response.json()))
        print(dumps(values))
        raise ValueError("Did not find exactly one widget")

    get_line_url = values[0]["extensionActions"][0]["uri"]

    values = search_for_key_value_pair(workday_response.json(), "label", "Expense Lines")

    if len(values) != 1:
        print(dumps(values))
        raise ValueError("Did not find exactly one widget")

    rows = values[0]["rows"]

    for row in rows:
        sync_expense_report_line(cookies, get_line_url, instance_id, row["id"], server, token)


def sync_worker(cookies: Dict[str, str], instance_id: str, server: str, token: str) -> None:
    """
    Sync a worker (user) from Workday to Loop
    """
    print(f"Retrieving worker {instance_id} from Workday")
    workday_response = get(
        url=f"https://wd5.myworkday.com/gatech/inst/1$37/247${instance_id}.htmld", cookies=cookies, timeout=(5, 5)
    )

    if workday_response.status_code != 200:
        print(workday_response.status_code)
        print(workday_response.text)
        raise ValueError("Unexpected response code from Workday")

    print(f"Uploading worker {instance_id} to Loop")

    loop_response = post(
        url=f"{server}/api/v1/workday/workers",
        json=workday_response.json(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=(5, 5),
    )

    if loop_response.status_code != 200:
        print(dumps(workday_response.json()))
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")


def sync_external_committee_member(cookies: Dict[str, str], instance_id: str, server: str, token: str) -> None:
    """
    Sync an external committee member from Workday to Loop
    """
    print(f"Retrieving external committee member {instance_id} from Workday")
    workday_response = post(
        url=f"https://wd5.myworkday.com/gatech/inst/1$15341/15341${instance_id}.htmld",
        cookies=cookies,
        data={"preview": 1},
        timeout=(5, 5),
    )

    if workday_response.status_code != 200:
        print(workday_response.status_code)
        print(workday_response.text)
        raise ValueError("Unexpected response code from Workday")

    print(f"Uploading external committee member {instance_id} to Loop")

    loop_response = post(
        url=f"{server}/api/v1/workday/external-committee-members",
        json=workday_response.json(),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        timeout=(5, 5),
    )

    if loop_response.status_code != 200:
        print(dumps(workday_response.json()))
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")


def main() -> None:
    """
    Entrypoint for script
    """
    parser = ArgumentParser(
        description="Upload data from Workday to Loop",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--server",
        help="the base URL of the Loop server",
        required=True,
    )
    parser.add_argument(
        "--token",
        help="the token to authenticate to Loop",
        required=True,
    )
    parser.add_argument(
        "--georgia-tech-username",
        help="the Georgia Tech username to authenticate to Workday",
        required=False,
    )
    parser.add_argument(
        "--georgia-tech-password",
        help="the Georgia Tech password to authenticate to Workday",
        required=False,
    )
    args = parser.parse_args()
    driver = webdriver.Chrome(service=Service(executable_path=ChromeDriverManager().install()))
    driver.maximize_window()

    log_in_to_workday(driver, args.georgia_tech_username, args.georgia_tech_password)
    chunking_url = search_for_expense_reports(driver)

    cookies = {}

    for cookie in driver.get_cookies():
        cookies[cookie["name"]] = cookie["value"]

    full_url = f"https://wd5.myworkday.com{chunking_url}.htmld"

    print(f"Retrieving all results from Workday - {full_url}")

    workday_response = post(url=full_url, cookies=cookies, data={"startRow": 1, "maxRows": 500}, timeout=(5, 60))

    if workday_response.status_code != 200:
        print(workday_response.status_code)
        print(workday_response.text)
        raise ValueError("Unexpected response code from Workday")

    print("Uploading results to Loop")

    loop_response = post(
        url=f"{args.server}/api/v1/workday/expense-reports",
        json=workday_response.json(),
        headers={
            "Authorization": f"Bearer {args.token}",
            "Accept": "application/json",
        },
        timeout=(5, 60),
    )

    if loop_response.status_code != 200:
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")

    print(loop_response.status_code)
    print(loop_response.json())

    for worker in loop_response.json()["workers"]:
        sync_worker(cookies, worker, args.server, args.token)

    for ecm in loop_response.json()["external-committee-members"]:
        sync_external_committee_member(cookies, ecm, args.server, args.token)

    for expense_report in loop_response.json()["expense-reports"]:
        sync_expense_report(cookies, expense_report, args.server, args.token)

    loop_response = get(
        url=f"{args.server}/api/v1/workday/sync",
        headers={
            "Authorization": f"Bearer {args.token}",
            "Accept": "application/json",
        },
        timeout=(5, 5),
    )

    if loop_response.status_code != 200:
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")

    print(loop_response.status_code)
    print(loop_response.json())

    for worker in loop_response.json()["workers"]:
        sync_worker(cookies, worker, args.server, args.token)

    for ecm in loop_response.json()["external-committee-members"]:
        sync_external_committee_member(cookies, ecm, args.server, args.token)

    for expense_report in loop_response.json()["expense-reports"]:
        sync_expense_report(cookies, expense_report, args.server, args.token)

    loop_response = post(
        url=f"{args.server}/api/v1/workday/sync",
        headers={
            "Authorization": f"Bearer {args.token}",
            "Accept": "application/json",
        },
        timeout=(5, 5),
    )

    if loop_response.status_code != 200:
        print(loop_response.status_code)
        print(loop_response.text)
        raise ValueError("Unexpected response code from Loop")


if __name__ == "__main__":
    main()
