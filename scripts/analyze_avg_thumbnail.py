'''
Constructs the average thumbnail from a list of YouTuber thumbnails.
'''
import os, shutil, requests, sys
import numpy as np
from PIL import Image
import scrapetube

########################### HELPERS ##################################
def scrape_video_ids(channelurl, sort_choice, limit_choice):
    """
    Args:
        channelurl (String): the URL to the channel (e.g., https://www.youtube.com/c/MrBeast6000)
        sort_choice (String): one of ["newest", "oldest", "popular"]
        limit_choice (int): number of videos to scrape
    Returns:
        A list of video IDs scraped
    """
    videos = scrapetube.get_channel(channel_url=channelurl, limit=limit_choice, sort_by=sort_choice)
    video_ids = [video['videoId'] for video in videos]
    return video_ids

def load_local_thumbnails(imdir, limit_choice):
    """
    Args:
        imdir (String): thumbnail directory
        limit_choice (int): number of videos to scrape
    Returns:
        An np array of Images as nparrays
    """
    # Access all PNG files in directory
    allfiles=os.listdir(imdir)
    imlist=[f"{imdir}/{filename}" for filename in allfiles if  filename[-4:] in [".jpg"]][0:limit_choice]
    return np.array([np.array(Image.open(im)) for im in imlist])

def download_thumbnails(channel_url_choice, sort_choice, limit_choice, imdir):
    """
    Args:
        channel_url_choice (String): url of the YouTube channel
        sort_choice (String): one of ["newest", "oldest", "popular"]
        limit_choice (int): number of videos to scrape
        imdir (String): thumbnail directory
    Returns:
        An array of Images as nparrays representing each thumbnail
    """
    # scrape the video IDs for use in downloading each thumbnail
    video_ids = scrape_video_ids(channel_url_choice, sort_choice, limit_choice)

    # download thumbnail & add to nparray
    # -- each image is an nparray representing the pixels of the thumbnail
    # -- goal: create an nparray that contains all thumbnails
    videos = []
    for index, video_id in enumerate(video_ids):
        # assumes the filename is `maxresdefault.jpg` from YouTube
        image_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        filename = f"{index}.jpg"

        # get the thumbnail from YouTube
        r = requests.get(image_url, stream = True)

        # check if the image was retrieved successfully
        if r.status_code == 200:
            # set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            
            # open a local file with wb (write binary) permission.
            # save in the thumbnails directory for this creator
            filepath = f"{imdir}/{filename}"
            with open(filepath, 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded:', filename)

            # add to the list of thumbnails
            videos.append(np.array(Image.open(filepath)))
        else:
            # ignore (but let it be known!)
            print('Image Couldn\'t be retreived')
    
    # should be a list of Images as nparrays
    return np.array(videos)

def average_thumbnail_basic(videos, outputdir, limit_choice, sort_choice):
    '''
    Args:
        videos (list of nparrays): an array of Images as nparrays representing each thumbnail
        outputdir (String): directory to store results
        limit_choice (int): number of videos to scrape
        sort_choice (String): one of ["newest", "oldest", "popular"]
    Returns:
        A single Image representing the average thumbnail (sum of all pixels / num thumbnails)
    '''
    arr = np.array(np.mean(videos, axis=(0)), dtype=np.uint8)
    out = Image.fromarray(arr, mode="RGB")
    out.show()
    out.save(f"{outputdir}{limit_choice}_{sort_choice}_average.jpg")
    return out

########################## DRIVER ###############################

# Answers the question: What do the 10 most recent Mr Beast thumbnails look like averaged together?
# TODO: input validation (too lazy right now!)
channel_name = sys.argv[1] # the name of the channel
channel_url_choice = sys.argv[2] # the url of the channel
sort_choice = sys.argv[3] # one of ["newest", "oldest", or "popular"]
limit_choice = int(sys.argv[4]) # number of videos to analyze
redownload = True # force a redownload of the thumbnails
imdir = f"../thumbnails/{channel_name}/{sort_choice}" # where the thumbnails are
outputdir = f"../thumbnails/{channel_name}/output/" # output results

# Either scrape & download or load from a local directory of thumbnails
if(redownload):
    os.makedirs(imdir, exist_ok=True)
    print("Scraping new thumbnails...")
    videos = download_thumbnails(channel_url_choice, sort_choice, limit_choice, imdir)
else:
    # Assume that we have pulled thumbnails in before
    # TODO: investigate thumbnail 16
    print("Using existing thumbnails...")
    try:
        videos = load_local_thumbnails(imdir, limit_choice)
    except:
        print("Error: retry with redownload == True")
        exit()

# Create the output directory if it doesn't exist
os.makedirs(outputdir, exist_ok=True)

# Run the averaging algorithm
average_thumbnail_basic(videos, outputdir, limit_choice, sort_choice)

# TODO: average by relative popularity (most popular = 1.0)