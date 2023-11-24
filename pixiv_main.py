# -*-coding:utf-8-*-
import getopt
import sys

from pixiv_gui_pyqt import MainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


def main(argv):
    """
    options, args = getopt.getopt(args, shortopts, longopts=[])
    参数args:一般是sys.argv[1:]。过滤掉sys.argv[0]，它是执行脚本的名字，不算做命令行参数。
    参数shortopts:短格式分析串。例如:"hp:i:",h后面没有冒号,表示后面不带参数;p和i后面带有冒号,表示后面带参数。
    参数longopts:长格式分析串列表。例如:["help", "ip=", "port="],help后面没有等号,表示后面不带参数;ip和port后面带等号,表示后面带参数。

    返回值options是以元组为元素的列表,每个元组的形式为：(选项串, 附加参数)，如：('-i', '192.168.0.1')
    返回值args是个列表,其中的元素是那些不含'-'或'--'的参数。
    """
    usegui = False
    password = ""
    try:
        # sys.argv[1:]为要处理的参数列表，sys.argv[0]为脚本名，所以用sys.argv[1:]过滤掉脚本名。
        opts, args = getopt.getopt(
            argv[1:], "hgp:", ["help", "g", "password="])
    except getopt.GetoptError:
        print("Error: test_arg.py -g <username> -p <password>")
        print("   or: test_arg.py --gui=<username> --password=<password>")
        sys.exit(2)

    # 处理 返回值options是以元组为元素的列表。
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("test_arg.py -g <username> -p <password>")
            print("or: test_arg.py --gui=<username> --password=<password>")
            sys.exit()
        elif opt in ("-g", "--gui"):
            usegui = True
        elif opt in ("-p", "--password"):
            password = arg
            print(password)

    # 打印 返回值args列表，即其中的元素是那些不含'-'或'--'的参数。
    # print(password)
    if usegui:
        # 获取屏幕的缩放比例
        scaleRate = QApplication.screens()[0].logicalDotsPerInch() / 96
        # print(scaleRate)
        app = QApplication(argv)  # 创建应用程序对象
        main_window = MainWindow(scaleRate)  # 创建主窗口
        main_window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    # 解决图片在不同分辨率显示模糊问题
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    main(sys.argv)
    # main()
