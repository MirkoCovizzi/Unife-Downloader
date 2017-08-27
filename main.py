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
import pdfkit

visited = []
root = True
page_to_pdf = True


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


def download(driver, directory):
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    div = soup.find_all('div', {'id': 'content-core'})
    document = div[0].span.a['href']
    response = requests.get(document, stream=True)
    file_name = re.sub('\s+', '', div[0].span.a.text)
    name, extension = os.path.splitext(file_name)
    num = 1;
    while os.path.isfile(directory + os.sep + name + extension):
        num += 1
        name += '_' + str(num)
    print("Downloading " + name + extension + "...")
    with open(directory + os.sep + name + extension, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)


def recursive_downloader(driver, directory=None):
    current_url = driver.current_url
    print(current_url)
    global root
    dir = directory
    page = driver.page_source
    soup = BeautifulSoup(page, 'html.parser')
    address_list = soup.find_all('a', {'class': 'contenttype-file state-missing-value url'})
    if len(address_list) != 0:
        if dir is None:
            dir = filedialog.askdirectory()
        for a in address_list:
            if a['href'] not in visited:
                visited.append(a['href'])
                driver.find_element_by_xpath('//a[@class="contenttype-file state-missing-value url"][contains(text(), "'
                                             + a.text + '")]').click()
                download(driver, dir)
                driver.back()
    folder_list = soup.find_all('a', {'class': 'contenttype-folder state-external url'})
    if len(folder_list) != 0:
        if dir is None:
            dir = filedialog.askdirectory()
        for f in folder_list:
            if f['href'] not in visited:
                visited.append(f['href'])
                path = dir + os.sep + f.text
                driver.find_element_by_xpath('//a[@class="contenttype-folder state-external url"][contains(text(), "'
                                             + f.text + '")]').click()
                if not os.path.exists(path):
                    print("Creating folder " + f.text)
                    os.makedirs(path)
                recursive_downloader(driver, path)
                driver.back()
    if root:
        root = False
        tree_list = soup.find_all('a', {'class': 'state-external navTreeFolderish contenttype-folder'})
        if len(tree_list) != 0:
            if dir is None:
                dir = filedialog.askdirectory()
            for t in tree_list:
                if t['href'] not in visited:
                    visited.append(t['href'])
                    path = dir + os.sep + t.span.text
                    driver.find_element_by_xpath('//a[@class="state-external navTreeFolderish contenttype-folder"]/'
                                                 'span[contains(text(), "'
                                                 + t.span.text + '")]').click()
                    if not os.path.exists(path):
                        print("Creating folder " + t.span.text)
                        os.makedirs(path)
                    recursive_downloader(driver, path)
                    driver.back()
    if len(address_list) + len(folder_list) == 0:
        print("Non sono presenti documenti all'indirizzo specificato.")
        if page_to_pdf and not directory is None:
            name = current_url.split('/')[-1]
            pdfkit.from_url(current_url, directory + os.sep + name + '.pdf')


def main():
    root = tk.Tk()
    root.withdraw()
    while True:
        url = input("Inserire URL del corso:")
        if url == "":
            sys.exit()
        if url.startswith('http://www.unife.it/'):
            driver = webdriver.PhantomJS()
            driver.get(url)
            break
        else:
            print("L'indirizzo inserito non è valido.")

    while True:
        driver.find_element_by_xpath('//a[@title="Accedi"]').click()
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        if soup.find('input', {'id': '__ac_name'}) is not None:
            username = InputDialog(root, text="Inserire Username:", title="Unife Downloader")
            root.wait_window(username)
            if username.value.get() == '':
                sys.exit()
            input_element_u = driver.find_element_by_id('__ac_name')
            input_element_u.clear()
            input_element_u.send_keys(username.value.get())
            password = InputDialog(root, text="Inserire Password:", password=True, title="Unife Downloader")
            root.wait_window(password)
            if password.value.get() == '':
                sys.exit()
            input_element_p = driver.find_element_by_id('__ac_password')
            input_element_p.send_keys(password.value.get())
            input_element_p.send_keys(Keys.ENTER)

            page = driver.page_source
            soup = BeautifulSoup(page, 'html.parser')
            if soup.find('dl', {'class': 'portalMessage error'}) is not None:
                messagebox.showerror("Unife Downloader", "Riconoscimento fallito. Sia il nome utente "
                                                         "che la password "
                                                         "tengono conto del maiuscolo/minuscolo, "
                                                         "controlla che il blocco delle maiuscole non sia attivato.")
                driver.back()
            if soup.find('a', {'id': 'user-name'}) is not None:
                break
        else:
            print('Errore: impossibile fare il login.')

    recursive_downloader(driver)
    driver.close()


if __name__ == '__main__':
    main()
