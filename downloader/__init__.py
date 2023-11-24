import downloader.withthreadpool
import downloader.withasyncio
Threadpool_Downloader = downloader.withthreadpool.Downloader
Asyncio_Downloader = downloader.withasyncio.Downloader
__all__ = ["Threadpool_Downloader", "Asyncio_Downloader"]
