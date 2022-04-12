import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

basic_url = 'https://books.toscrape.com' # Books to Scrape basic url
product_url= f'{basic_url}/catalogue/' # Basic product url


""" Product image download"""
def download_images(image_url,title):
    SAVE_FOLDER = 'images'
    pattern = r'[^A-Za-z0-9]+'
    # title refactoring to be a valid image name
    title = re.sub(pattern, '', title)
    imagename = SAVE_FOLDER + '/' + title + '.jpg'
    response = requests.get(image_url).content

    with open(imagename, 'wb+') as file:
        file.write(response)


""" Get all categroies"""
def get_all_categories(url):
    categories = []
    response = requests.get(url)
    categories_l = BeautifulSoup(response.text, 'html.parser').find('ul', class_="nav nav-list").find('li').find('ul').find_all('a', href=True)
    for category in categories_l: 
        category_name = category
        link = category["href"]
        category_url = f'{basic_url}/{link}'
        categories.append({'category_name': category_name.text.strip(), 'category_url': category_url})
        
    df = pd.DataFrame.from_dict(categories)
    df.to_csv(r'categories_data.csv', index=False)

    return categories


""" Get books in category"""
def get_all_books_by_category(url):
    books_list = []
    response = requests.get(url)
    books = BeautifulSoup(response.text, 'html.parser').find_all('div', attrs = {'class': "image_container"})
    button_next = BeautifulSoup(response.text, 'html.parser').find_all('li', attrs={'class': 'next'})
    # Check if category page have a next page button
    for btn in button_next:
            # Modify url to get next page
            link = btn.a['href']
            url_splitted = url.split("/")
            url_splitted[-1] = link
            next_url = "/".join(url_splitted)

    for b in books:
        book = b.a['href']
        book_link_refactor = f'{product_url}{str(book).strip("/../../../")}'
        books_list.append(book_link_refactor)
    
    if button_next :
        # If category contains multi pages recall the function with the new url to get next books
        books_list.extend(get_all_books_by_category(next_url))

    return books_list


def get_book_data(url):
    result = []
    class_second_part = {'Zero': 0,'One': 1,'Two': 2,'Three': 3, 'Four': 4, 'Five': 5}
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    product_title = soup.find('h1')
    title = product_title.string
    product_url = url
    product_description = soup.find('div', class_="sub-header").find_next('p')
    description = product_description.string
    img_tag = soup.find('img')
    imageSrc = img_tag.get('src')
    imageUrl = f'{basic_url}/{imageSrc}'     
    tds = soup.table.find_all('td')
    upc = tds[0].text
    price_excl_tax = tds[2].text
    price_incl_tax = tds[3].text
    tax = tds[4].text
    availability = tds[5].text
    reviews = tds[6].text
    for i in soup.find('div', class_="col-sm-6 product_main").select("p:nth-of-type(3)"):
        reating = i['class']
    rating = reating[1]
    review_rating = f'{class_second_part[rating]} stars'

    result.append({'product_url ': product_url, 'universal_ product_code (upc)': upc, 'title' : title, 'price_including_tax': price_incl_tax, 'Price (excl. tax)': price_excl_tax, 'url_image' : imageUrl, 'Description':description,  
                    'Tax': tax, 'Availability': availability, 'Number of reviews': reviews, 'review_rating': review_rating})
    # print(result)
    download_images(imageUrl, title)

    return result



categories = get_all_categories(basic_url)

for category in categories:
    book_info = []

    # Use category name as csv file name
    csv_name = category["category_name"]
    category_url = category['category_url']

    # In books var save all products in category 
    books = get_all_books_by_category(category_url)

    for book in books :
        data = get_book_data(book)
        book_info.extend(data)
    # Change default csv delimiter to avoid sep=';'        
    df = pd.DataFrame(book_info)
    df.to_csv(f'{csv_name}.csv', index=False, sep=';')
        