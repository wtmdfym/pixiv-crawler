# -*-coding:utf-8-*-
import downloader.withthreadpool
import downloader.withasyncio
ThreadpoolDownloader = downloader.withthreadpool.Downloader
AsyncioDownloader = downloader.withasyncio.Downloader
AsyncioDownloaderHttpx = downloader.withasyncio.DownloaderHttpx
__all__ = ["ThreadpoolDownloader", "AsyncioDownloader"]
