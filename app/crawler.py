from bs4 import BeautifulSoup as bs
import requests
import constants


def get_related_video_url(input_url):
    # check if is youtube or soundcloud link
    return_link = constants.EMPTY_INPUT

    # get link
    page = requests.get(input_url)
    soup = bs(page.content, 'html.parser')

    if constants.YOUTUBE in input_url:
        search_class = constants.CONTENT_LINK
        send_url = constants.YOUTUBE
    elif constants.SOUNDCLOUD in input_url:
        search_class = constants.SIDE_BAR
        send_url = constants.SOUNDCLOUD
    else:
        return return_link

    # get list of related links
    related_links = soup.find_all('a', {'class': search_class})

    # get the first TODO: check to see if we've already played the song, if so go to the next song
    if related_links is not None and len(related_links) > 0:
        return_link = constants.HTTPS + send_url + related_links[0].get('href')

    return return_link
