#!/usr/bin/env python
# coding: utf-8

#Import Dependencies
from bs4 import BeautifulSoup as bs
from splinter import Browser
import pandas as pd
import datetime as dt  
import pymongo


### NASA MARS NEWS

def mars_news(browser):
    url = 'https://mars.nasa.gov/news/'
    browser.visit(url)

    #get first list item and wait half a second if not imediately present
    browser.is_element_present_by_css('ul.item-list li.slide', wait_time = 0.5)
    html = browser.html
    news_soup = bs(html, 'html.parser')
 
    try:
        slide = news_soup.select_one('ul.item_list li.slide') 
        slide.find("div", class_= "content_title")


        news_title = slide.find('div', class_="content_title").get_text()
        news_paragraph = slide.find('div', class_="article_teaser_body").get_text()
    except AttributeError:
        return None, None
    return news_title, news_paragraph


# ### JPL SPACE IMAGES FEATURED IMAGES

def featured_images(browser):
    url = 'https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars'
    browser.visit(url)
    full_image_button = browser.find_by_id("full_image")
    full_image_button.click()
    
    browser.is_element_present_by_text('more info', wait_time=1)
    more_info_button = browser.find_link_by_partial_text('more info') 
    more_info_button.click()

    html = browser.html
    image_soup = bs(html, 'html.parser')

    img = image_soup.select_one('figure.lede a img')
    try:
        img_url = img.get('src')
    except AttributeError:
        return None
    img_url = f'https://www.jpl.nasa.gov{img_url}'
    return img_url

# ### MARS WEATHER

def twitter_weather(browser):
    url = 'https://twitter.com/marswxreport?lang=en'
    browser.visit(url)
    html = browser.html
    weather_soup = bs(html, 'html.parser')

    mars_weather_tweet = weather_soup.find('div', attrs = {"class": "tweet", "data-name": "Mars Weather"}) 

    mars_weather = mars_weather_tweet.find('p', 'tweet-text').get_text()
    return mars_weather


# ### MARS HEMISPHERES

def hemisphere(browser):
    url = 'https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars'
    browser.visit(url)
    hem_image_url = []
    
    links = browser.find_by_css('a.product-item h3')
    for item in range(len(links)):
        hemisphere = {}
        browser.find_by_css('a.product-item h3')[item].click()
    
    # Find a sample image anchor tag and extract the href
        sample_element = browser.find_link_by_text('Sample').first
        hemisphere['img_url'] = sample_element['href']
    
    # Get hemisphere title
        hemisphere['title'] = browser.find_by_css('h2.title').text
    
    # Append hemisphere object to list
        hem_image_url.append(hemisphere)
    
    # Navigate backwords
        browser.back()
    
    return hem_image_url

def scrape_hemisphere(html_text):
    hemisphere_soup = bs(html_text, 'html.parser')
    try:
        title_element = hemisphere_soup.find('h2', class_='title').get_text()
        sample_element = hemisphere_soup.find('a', text = 'Sample').get('href')
    except AttributeError:
        title_element = None
        sample_element = None
    hemisphere = {
        "title" : title_element,
        "img_url" : sample_element
    }
    return hemisphere


### MARS FACTS
def mars_facts():
    try:
        df = pd.read_html('https://space-facts.com/mars/')[0]
    except BaseException:
        return None
    df.columns = ['description', 'value']
    df.set_index('description', inplace = True)

# Use Pandas to convert the data to a HTML table string
    return df.to_html(classes = 'table table-striped')



def scrape_all(): # main bot should be on the bottom, to execute all the functions

    executable_path = {'executable_path': '/usr/local/bin/chromedriver'}
    browser = Browser('chrome', **executable_path, headless=False)
    news_title, news_paragraph = mars_news(browser)
    img_url = featured_images(browser)
    mars_weather = twitter_weather(browser)
    hem_image_url = hemisphere(browser)
    facts = mars_facts()
    timestamp = dt.datetime.now()

    mars_data = {
        "news_title" : news_title,
        "news_paragraph": news_paragraph,
        "featured_image" : img_url,
        "hemisphere" : hem_image_url, 
        "facts" : facts,
        "weather": mars_weather,
        "last modified": timestamp
    }
    
    browser.quit()
    return mars_data
if __name__ == "__main__":
    con = pymongo.MongoClient("mongodb://localhost:27017/mars_app")
    coll = con.db.mars
    data = scrape_all()
    coll.insert_one(data)
