# -*-coding:utf-8-*-
#
# @file __init__.py
#
import infofetcher.followinginfo
import infofetcher.imageinfo
FollowingsRecorder = infofetcher.followinginfo.FollowingsRecorder
InfoFetcher = infofetcher.imageinfo.InfoFetcher
InfoFetcherHttpx = infofetcher.imageinfo.InfoFetcherHttpx
InfoGetterOld = infofetcher.imageinfo.InfoGetter_old
__all__ = ["FollowingsRecorder", "InfoFetcher"]
