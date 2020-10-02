import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import sys


def thread_page_crawl(soup, start_date=None):
    sb_name = soup.find('h2').select_one('a').text

    posts_list = []
    containers = soup.find_all('div', class_='comment-right-container')  # date is in container
    posts = soup.find_all('div', class_='comment-right')
    for post, container in zip(posts, containers):
        date_text = container.find('div').get_text()
        date = datetime.strptime(date_text, "%a %b %d, %Y %I:%M %p")
        if start_date is not None and date < start_date:
            continue
        username = post.find_all('div')[1].select_one('a').text
        post_content = post.find_all('div', class_='post-text')[0].get_text("\n")

        posts_list.append([username, sb_name, len(post_content.split()), date])

    return posts_list


def get_next_page(soup):
    link = None
    pagination = soup.find("div", class_='pagination')
    span = pagination.find("span")
    if span is not None:
        for i in range(len(span.contents)):
            if span.contents[i].name == 'strong' and i < len(span.contents) - 2:
                link = span.contents[i + 2]['href'][1:]
                break
    return link


def thread_crawl(link, start_date=None):
    start_url = 'https://www.youngwriterssociety.com'
    link = link[1:]

    posts_list = []
    pages_crawled = 0
    while link is not None:
        # get page
        page = requests.get(start_url + link)
        soup = BeautifulSoup(page.content, 'html.parser')
        # parse posts
        posts_list.extend(thread_page_crawl(soup, start_date))
        pages_crawled += 1
        link = get_next_page(soup)

    return posts_list


def scrape_forum(forum_url, start_date=None):
    topics = []
    dates = []
    link = forum_url
    while link is not None:
        page = requests.get(STORYBOOKS_URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        rows = soup.find_all('li', class_="row bg1")  # makes sure we only get normal threads, not announcements or stickies
        for row in rows:
            topics.append(row.find('a', class_='topictitle', href=True)['href'])  # finds the < a > link for each thread
            last_post_date = row.find('dd', class_='lastpost').get_text().split("\n")[1]
            date = datetime.strptime(last_post_date, "  %a %b %d, %Y %I:%M %p")
            dates.append(date)
        link = get_next_page(soup)

    posts_list = []
    for topic in topics:
        posts_list.extend(thread_crawl(topic, start_date))

    all_posts = pd.DataFrame(posts_list, columns=["Username", "SB", "Word Count", "Date"])
    return all_posts


if __name__ == '__main__':
    month = "09/2020"
    date = None
    try:
        date = datetime.strptime(month, "%m/%Y")
    except ValueError:
        print("Month must be in format MM/YYYY")
        exit(1)

    STORYBOOKS_URL = "https://www.youngwriterssociety.com/viewforum.php?f=7"
    storybook_posts = scrape_forum(STORYBOOKS_URL, date)

    print("Data since:", date)
    print("Storybook Forums:")
    print(storybook_posts['SB'].value_counts(descending=True))
    print()
    # print users data
    print("Users:")
    print(storybook_posts['Username'].value_counts(descending=True))

