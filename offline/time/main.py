#!/usr/bin/python

#!/usr/bin/python

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyAey-bnryq7CIv7jRNRSz9WYXxvkxugbkY"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def youtube_search(options):
  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  # Call the search.list method to retrieve results matching the specified
  # query term.
  search_response = youtube.search().list(
    #q=options.q,
    type="video",
    #location=options.location,
    #locationRadius=options.location_radius,
    part="id",
    maxResults=options.max_results
  ).execute()

  search_videos = []

  # Merge video ids
  for search_result in search_response.get("items", []):
    search_videos.append(search_result["id"]["videoId"])
  video_ids = ",".join(search_videos)

  # Call the videos.list method to retrieve location details for each video.
  video_response = youtube.videos().list(
    id=video_ids,
    part='id'
  ).execute()

  videos = []

  # Add each result to the list, and then display the list of matching videos.
  for video_result in video_response.get("items", []):
    videos.append("%s" % video_result["id"])

  print(("Videos:\n", "\n".join(videos), "\n"))


if __name__ == "__main__":
  argparser.add_argument("--q", help="Search term", default="Google")

  argparser.add_argument("--location-radius", help="Location radius", default="5km")
  argparser.add_argument("--max-results", help="Max results", default=50)
  args = argparser.parse_args()

  try:
    youtube_search(args)
  except HttpError as e:
    print(("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)))
