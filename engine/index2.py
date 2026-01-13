from DrissionPage import ChromiumOptions, ChromiumPage
import os
from pathlib import Path
import time
import requests
import csv

from DrissionPage import SessionPage


# 添加断点续传下载功能
def resume_download(url, save_path, filename=None):
    """
    支持断点续传的下载函数
    :param url: 下载链接
    :param save_path: 保存路径（目录）
    :param filename: 保存的文件名（可选，如果不提供则从URL中提取）
    :return: 下载文件的完整路径
    """
    if filename is None:
        # 从URL中提取文件名
        filename = url.split('/')[-1]
        if not filename or '.' not in filename:
            filename = "downloaded_file.pdf"

    # 确保保存目录存在
    full_save_path = Path(save_path)
    full_save_path.mkdir(parents=True, exist_ok=True)

    # 完整的文件路径
    file_path = full_save_path / filename

    # 获取已下载文件的大小
    if file_path.exists():
        downloaded_size = file_path.stat().st_size
        headers = {'Range': f'bytes={downloaded_size}-'}
        print(f"检测到已下载部分，继续下载。已下载大小: {downloaded_size} bytes")
    else:
        downloaded_size = 0
        headers = {}
        print("开始新下载...")

    # 发起请求
    response = requests.get(url, headers=headers, stream=True)

    # 检查服务器是否支持断点续传
    if response.status_code == 206:  # 206 Partial Content 表示支持断点续传
        mode = 'ab'  # 追加模式
    elif response.status_code == 200 and downloaded_size == 0:
        mode = 'wb'  # 写入模式
    elif response.status_code == 200 and downloaded_size > 0:
        # 如果服务器不支持断点续传，但本地文件存在，重新下载
        print("服务器不支持断点续传，重新下载文件")
        downloaded_size = 0
        mode = 'wb'
    else:
        print(f"下载请求失败，状态码: {response.status_code}")
        return None

    # 获取文件总大小
    total_size = int(response.headers.get('content-length', 0))
    if response.status_code == 206:  # 断点续传
        total_size += downloaded_size  # 加上已下载的部分

    print(f"文件总大小: {total_size} bytes, 已下载: {downloaded_size} bytes")

    # 下载文件
    with open(file_path, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded_size += len(chunk)
                # 显示进度
                if total_size > 0:
                    progress = (downloaded_size / total_size) * 100
                    print(f"\r下载进度: {progress:.1f}% ({downloaded_size}/{total_size} bytes)", end="")

    print(f"\n下载完成: {file_path}")
    return str(file_path)


###自动化逻辑
def main():
    # categories_list = ['diesels', 'machinery', 'auxiliary']  ##三个大类
    categories_list = ['machinery']
    for category_name in categories_list:
        page.get(f'https://engine.od.ua/{category_name}')
        products(page, category_name)  # 传递类别名称


def products(page, category_name):  # 小类遍历
    products_list = page.ele('@id=wrapper').children()
    for product in products_list:
        print(product.attr('href'))
        href = product.attr('href')  # 小类名
        single_product(href, category_name)


def single_product(href, category_name):
    try:

        page2 = page.new_tab(href)
        btus = page2.eles('@class=pull-center panel panel-default')
        main_product_name =  page2.ele('@@class=text-center@@tag():h1').text
        # 获取当前页面的主产品名称
        cleaned_main_product_name = clean_filename(main_product_name)
        
        # 检查 ./{category_name}/{main_product_name} 文件夹是否为空，如果是空的执行下面爬虫程序，不是空的就跳过
        main_product_dir = Path(f"./{category_name}/{cleaned_main_product_name}")
        if not is_directory_empty(main_product_dir):
            print(f"跳过 {cleaned_main_product_name}，目录已存在且非空")
            page2.close()
            return  # 跳过整个主产品
        
        for btu in btus:
            btu=btu.ele('tag:a')
            href=btu.attr('href')
            page1=page.new_tab(href)
            but_final=page1.ele('@class=pull-center panel panel-default')
            product_name = page1.ele('@@class=text-center@@tag():h1').text
            # 清理产品名称中的非法字符
            cleaned_product_name = clean_filename(product_name)

            # 获取当前页面的分类名称作为子分类名
            subcategory_name = cleaned_product_name

            # 修改保存路径结构为: ./{category_name}/{main_product}/{subcategory}/

            save_dir = Path(f"./{category_name}/{cleaned_main_product_name}/{subcategory_name}")
            save_dir.mkdir(parents=True, exist_ok=True)

            product_name = page1.ele('@@class=text-center@@tag():h1').text
            # 初始化CSV数据列表
            csv_data = []

            # 获取产品信息
            # 这里有两种情况 一种是表格的  一种是贴图的
            tables = page1.ele('@class=table table-responsive table-hover table-bordered table-striped')
            if tables:
                trs = tables.child().children()
                for tr in trs:
                    columns = tr.children()

                    # 检查是否有足够的列数
                    if len(columns) < 3:
                        continue  # 跳过列数不足的行（如表头行）

                    id = columns[0].text
                    model = columns[1].text
                    description = columns[2].text
                    pdf_href = ''

                    # 检查是否包含PDF下载链接
                    if 'Free download.' in description:
                        try:
                            # 尝试获取PDF链接
                            pdf_element = columns[2].ele('tag:a')
                            if pdf_element:
                                pdf_href = pdf_element.attr('href')

                            # 如果上面没有找到，尝试从下一个元素获取
                            if not pdf_href:
                                next_element = columns[2].next()
                                if next_element:
                                    pdf_href = next_element.attr('href')

                            # 如果找到PDF链接，下载文件
                            if pdf_href:
                                url = pdf_href
                                # 修改保存路径，使用新的目录结构
                                save_path = f'./{category_name}/{cleaned_main_product_name}/{subcategory_name}/'
                                # 使用新的断点续传下载函数
                                res = resume_download(url, save_path)  # 下载pdf
                                print(res)

                        except Exception as e:
                            print(f"下载PDF时出错: {e}")

                    # 将数据添加到列表中
                    csv_data.append([id, model, description, pdf_href])

                # 一次性保存所有数据到CSV文件
                if csv_data:
                    # 修改CSV文件保存路径，使用新的目录结构
                    csv_filepath = f'./{category_name}/{cleaned_main_product_name}/{subcategory_name}/{subcategory_name}.csv'
                    save_to_csv(csv_data, csv_filepath)

                print(f"已保存 {len(csv_data)} 条记录到 {subcategory_name}.csv")


            page1.close()
    except Exception as e:
        print(f"处理页面时出错: {e}")
        if 'page1' in locals():
            page1.close()


def is_directory_empty(directory_path):
    """
    检查目录是否为空
    :param directory_path: 目录路径
    :return: 如果目录不存在或为空则返回True，否则返回False
    """
    path = Path(directory_path)
    if not path.exists():
        return True  # 目录不存在，认为是空的
    try:
        # 检查目录是否为空（包括子目录）
        if not any(path.iterdir()):
            return True  # 目录为空
        else:
            return False  # 目录不为空
    except PermissionError:
        print(f"无法访问目录 {directory_path}，权限不足")
        return False  # 权限不足时认为目录不为空，以避免跳过可能需要处理的目录


def save_to_csv(data, filepath):
    """将数据保存到CSV文件"""
    # 确保目录存在
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Model', 'Description', 'PDF_File'])  # 表头
        writer.writerows(data)


def clean_filename(filename):
    """
    清理文件名中的非法字符
    Windows 文件名不能包含以下字符: < > : " | ? * /
    同时移除换行符和回车符
    """
    # 替换非法字符
    illegal_chars = ['<', '>', ':', '"', '|', '?', '*', '/', '\n', '\r', '\t']
    cleaned = filename
    for char in illegal_chars:
        cleaned = cleaned.replace(char, '_')  # 将非法字符替换为下划线

    # 移除首尾空格
    cleaned = cleaned.strip()

    # 限制文件名长度（Windows 有 255 字符限制）
    if len(cleaned) > 200:  # 留出一些余地用于扩展名
        cleaned = cleaned[:200]

    return cleaned


if __name__ == '__main__':
    download_page = SessionPage()
    page = ChromiumPage()
    main()
    page.quit()  # 确保关闭浏览器