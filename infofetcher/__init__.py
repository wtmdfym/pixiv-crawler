#
# @file __init__.py
#
import infofetcher.followings
import infofetcher.imageinfo
FollowingsRecorder = infofetcher.followings.FollowingsRecorder
InfoGetter = infofetcher.imageinfo.InfoGetter
__all__ = ["FollowingsRecorder", "InfoGetter"]
