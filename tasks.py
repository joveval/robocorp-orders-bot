from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from robocorp import log
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    browser.configure(
        slowmo=100,
        headless=False,
    )

    open_robot_order_website("https://robotsparebinindustries.com/#/robot-order")
    orders = get_orders("https://robotsparebinindustries.com/orders.csv")

    for order in orders:
        close_annoying_modal()
        log.info("Order number:",str(order["Order number"]))
        fill_form(order)
        handle_error()
        pdf_file = store_receipt_as_pdf(order["Order number"])
        screenshot_file = screenshot_robot(order["Order number"])
        embed_screenshot_to_receipt(pdf_file=pdf_file,screenshot=screenshot_file)
        create_another_order()
        archive_receipts()


def archive_receipts():
    """ ZIP orders """
    archive = Archive()
    archive.archive_folder_with_zip(folder="output/receipts",archive_name="output/receipts.zip")

def create_another_order():
    """ Create next order clean up """
    page = browser.page()
    page.click("#order-another")


def handle_error():
    """ Handle warning alert """

    page = browser.page()

    error_raised = True
    while error_raised == True:
        error_raised=page.locator('css=.alert-danger').is_visible(timeout=3000)
        if error_raised:
            page.click("#order")


def open_robot_order_website(order_website_url):
    """ Go to robot order website """
    
    browser.goto(order_website_url)


def close_annoying_modal():
    """ Close modal window """
    
    page = browser.page()
    ok_element = page.locator('text="OK"').element_handle()
    ok_element.click()

def get_orders(csv_url):
    """ Get orders from CSV file """

    # Download CSV file

    http = HTTP()
    csv_file_path = "output/orders.csv"
    http.download(url=csv_url,target_file=csv_file_path,overwrite=True)

    # Read CSV as table
    tables = Tables()
    return tables.read_table_from_csv(path=csv_file_path)

def fill_form(data_row):
    """ Fill form based on data row """
    page = browser.page()

    page.select_option("#head",str(data_row["Head"]))
    page.check('xpath=//input[@id="id-body-'+str(data_row["Body"])+'"]')
    #page.fill('xpath=//input[placeholder="Enter the part number for the legs"]',str(data_row["Legs"]))
    
    page.fill('xpath=/html/body/div/div/div[1]/div/div[1]/form/div[3]/input',str(data_row["Legs"]))
    page.fill("#address",data_row["Address"])
    page.click("#preview")
    page.click("#order")


def store_receipt_as_pdf(order_number):
    """ Store receipt as a PDF file. """
    
    filepath = "output/receipts/receipt_"+str(order_number)+".pdf"
    
    page = browser.page()
    html_element = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf.html_to_pdf(html_element,filepath)

    return filepath

def screenshot_robot(order_number):
    """ Screenshot robot """
    filepath = "output/robots/screenshot_"+str(order_number)+".png"
    page = browser.page()
    html_element = page.locator("#robot-preview-image").element_handle()
    html_element.screenshot(path=filepath,type="png")
    return filepath

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """ Merge pdf + screenshot """
    
    pdf = PDF()
    pdf.add_files_to_pdf(
        files=[pdf_file+":1",screenshot+":align=center"],
        target_document=pdf_file
    )

