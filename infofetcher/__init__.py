# -*-coding:utf-8-*-
#
# @file __init__.py
#
import infofetcher.followinginfo
import infofetcher.imageinfo
FollowingsRecorder = infofetcher.followinginfo.FollowingsRecorder
InfoFetcherHttpx = infofetcher.imageinfo.InfoFetcherHttpx
__all__ = ["FollowingsRecorder", "InfoFetcherHttpx"]
