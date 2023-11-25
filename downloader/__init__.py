# -*-coding:utf-8-*-
import downloader.withthreadpool
import downloader.withasyncio
ThreadpoolDownloader = downloader.withthreadpool.Downloader
AsyncioDownloader = downloader.withasyncio.Downloader
__all__ = ["ThreadpoolDownloader", "AsyncioDownloader"]
