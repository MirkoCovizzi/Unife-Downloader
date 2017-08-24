from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import requests
import shutil
from tkinter import filedialog, messagebox
import tkinter as tk
import tkinter.ttk as ttk
import os
import sys
import re


class InputDialog(tk.Toplevel):
    def __init__(self, *args, text=None, password=False, title=None, **kwargs):
        super(InputDialog, self).__init__(*args, **kwargs)
        self.value = tk.StringVar()
        self.minsize(width=300, height=50)
        self.resizable(width=0, height=0)
        self.title(title)
        ttk.Label(self, text=text).pack(side='top')
        self.e = ttk.Entry(self, width=50)
        self.e.focus_set()
        if password:
            self.e['show'] = '*'
        self.e.pack(padx=5)
        ttk.Button(self, text="OK", command=self.on_button_press).pack(pady=5)
        self.bind_all('<Return>', self.on_return)

    def on_return(self, event):
        self.on_button_press()

    def on_button_press(self):
        self.value.set(self.e.get())
        self.destroy()


def download(address, driver, folder):
    driver.find_element_by_xpath('//a[@class="contenttype-file state-missing-value url"][contains(text(), "'
                                 + address.text + '")]').click()
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    div = soup.find_all('div', {'id': 'content-core'})
    document = div[0].span.a['href']
    response = requests.get(document, stream=True)
    file_name = re.sub('\s+', '', div[0].span.a.text)
    print("Downloading " + file_name + "...")
    with open(folder + os.sep + file_name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    driver.back()


def main():
    root = tk.Tk()
    root.withdraw()
    while True:
        url = InputDialog(root, text="Inserire URL relativa al materiale didattico:", title="Unife Downloader")
        root.wait_window(url)
        driver = webdriver.PhantomJS()
        if url.value.get() == '':
            sys.exit()
        if url.value.get().startswith('http://www.unife.it/'):
            driver.get(url.value.get())
            break
        else:
            messagebox.showerror("Unife Downloader", "L'indirizzo inserito non è valido.")
            driver.close()
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    if soup.find('input', {'id': '__ac_name'}) is not None:
        username = InputDialog(root, text="Inserire Username:", title="Unife Downloader")
        root.wait_window(username)
        if username.value.get() == '':
            sys.exit()
        input_element_u = driver.find_element_by_id('__ac_name')
        input_element_u.send_keys(username.value.get())
        password = InputDialog(root, text="Inserire Password:", password=True, title="Unife Downloader")
        root.wait_window(password)
        if password.value.get() == '':
            sys.exit()
        input_element_p = driver.find_element_by_id('__ac_password')
        input_element_p.send_keys(password.value.get())
        input_element_p.send_keys(Keys.ENTER)

    folder = filedialog.askdirectory()
    if not folder == '':
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        address_list = soup.find_all('a', {'class': 'contenttype-file state-missing-value url'})
        if len(address_list) != 0:
            for address in address_list:
                download(address, driver, folder)
        else:
            messagebox.showinfo("Unife Downloader", "Non sono presenti documenti all'indirizzo specificato.")
    driver.close()


if __name__ == '__main__':
    main()
