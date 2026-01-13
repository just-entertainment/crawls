import time
import csv
import json
import os
from datetime import datetime
from DrissionPage import ChromiumPage
import re
from DrissionPage import ChromiumOptions

path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'  # 请改为你电脑内Chrome可执行文件路径
ChromiumOptions().set_browser_path(path).save()


c_tab= ChromiumPage()
c_tab.get('http://m.ttship.com/login.html?from=http://info.ttship.com/index.html')
account= c_tab.ele('@name=account').input('17822058336')
password= c_tab.ele('@name=password').input('xzd888999')
login= c_tab.ele('@class=login-btn').click()


# 定义进度文件
PROGRESS_FILE = 'crawl_progress.json'
CSV_DIR = 'csv_files'  # 存储CSV文件的目录

# 确保CSV目录存在
os.makedirs(CSV_DIR, exist_ok=True)

# 获取最新的CSV文件
def get_latest_csv():
    csv_files = [f for f in os.listdir(CSV_DIR) if f.startswith('ship_info_') and f.endswith('.csv')]
    if not csv_files:
        return None
    # 按时间排序，获取最新的CSV文件
    csv_files.sort(reverse=True)
    return os.path.join(CSV_DIR, csv_files[0])

# 获取上一次CSV文件的第一条数据作为最新数据标识
def get_lastest_data_identifier():
    latest_csv = get_latest_csv()
    if not latest_csv:
        return None
    
    try:
        with open(latest_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            first_row = next(reader, None)
            if first_row:
                # 从ship_details中提取更新时间作为标识符
                ship_details = first_row.get('ship_name', '')
                update_time = extract_update_time(ship_details)
                return update_time
    except Exception as e:
        print(f"读取最新CSV文件失败: {e}")
        return None

# 从ship_details中提取更新时间的函数
def extract_update_time(ship_details):
    # 匹配 "更新时间：" 后面的日期时间格式，允许各种空格情况
    # 尝试多种可能的格式
    patterns = [
        r"更新时间：\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})",  # "更新时间：YYYY-MM-DD HH:MM:SS"
        r"更新时间：(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})",  # "更新时间:YYYY-MM-DD HH:MM:SS" (无空格)
        r"更新时间：\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",  # 另一种可能格式
    ]

    for pattern in patterns:
        match = re.search(pattern, ship_details)
        if match:
            return match.group(1).strip()  # 返回匹配的日期时间并去除空格

    # 如果以上都没匹配到，尝试更通用的模式查找日期时间格式
    general_pattern = r"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"
    match = re.search(general_pattern, ship_details)
    if match:
        # 检查是否紧跟在"更新时间："之后
        pos = ship_details.find(match.group(1))
        if pos > 0:
            before_time = ship_details[max(0, pos - 20):pos]  # 检查时间前的一些字符
            if "更新时间：" in before_time or "更新时间:" in before_time:
                return match.group(1).strip()

    return ""

# 尝试加载之前的进度
def load_progress():
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            return progress.get('current_page', 1), progress.get('current_index', 0)
    except FileNotFoundError:
        return 1, 0


# 保存进度
def save_progress(page, index):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'current_page': page, 'current_index': index}, f)

lastest_identifier = get_lastest_data_identifier()
# 从进度文件加载页码和索引
start_page, start_index = load_progress()

# 获取当前时间戳作为CSV文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
csv_filename = os.path.join(CSV_DIR, f'ship_info_{timestamp}.csv')

# 打开CSV文件准备写入
with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:  # 使用写入模式而非追加
    fieldnames = ['page_num', 'item_index', 'ship_name', 'contact_phone', 'ship_details', 'image_urls', 'info_title',
                  'info_price']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    # 写入表头
    writer.writeheader()

    tab = ChromiumPage()
    try:
        for i in range(0,10):
            cookies = c_tab.cookies()
            tab.set.cookies(cookies[i])
    except:
        pass
    tab.get('http://info.ttship.com/info/shipSell_1/cblx_0/cjs_0/hq_0.html')
    # 获取上次的最新数据标识

    print(f"上次最新数据标识: {lastest_identifier}")
    
    # 标记是否找到上次的最新数据
    found_lastest = False
    new_data_count = 0  # 记录新数据的数量

    for page in range(start_page, 1530):
        tab.get(f'http://info.ttship.com/info/shipSell_{page}/cblx_0/cjs_0/hq_0.html')
        table = tab.ele('@class=table table-hover')
        tab_list = table.child(index=2).children()

        # 如果是起始页，从上次中断的索引开始
        start_idx = start_index if page == start_page else 0

        for idx in range(start_idx, len(tab_list)):
            td = tab_list[idx]
            print(f"正在处理第 {page} 页，第 {idx + 1} 个...")

            try:
                href = td.ele('tag:a').attr('href')
                new_tab = tab.new_tab(href)
                
                shipTxt = new_tab.ele('@class=shipTxt').text
                click_tel = new_tab.ele('@class=telTxt').click()
                time.sleep(0.1)
                linkPhone = new_tab.ele('@name=linkPhone').text
                print(linkPhone)

                # 获取标题和价格信息
                try:
                    infoTitle = new_tab.ele('@class=infoTitle').text
                except Exception:
                    infoTitle = ''

                try:
                    infoPrice = new_tab.ele('@class=infoPrice').text
                except Exception:
                    infoPrice = ''

                shipDetailCon_ele = new_tab.ele('@class=shipDetailCon')
                shipDetailCon = new_tab.ele('@class=shipDetailCon').text

                # 从shipDetailCon中提取更新时间
                current_update_time = extract_update_time(shipTxt)

                # 收集图片URL
                image_urls = []
                if shipDetailCon_ele:
                    try:
                        images = shipDetailCon_ele.eles('tag:img', timeout=2)
                        for img in images:
                            src = img.attr('src')
                            if src:  # 确保src不为空
                                image_urls.append(src)
                                print(src)
                    except Exception as e:
                        print(f"收集图片URL时出错: {e}")
                        
            except Exception as e:
                print(f"提取船舶信息时出错: {e}")
                if 'new_tab' in locals():
                    new_tab.close()
                continue  # 跳过当前项，继续下一项

            # 检查更新时间是否与上次的最新数据匹配
            if lastest_identifier and current_update_time == lastest_identifier and not found_lastest:
                found_lastest = True
                print(f"已找到上次的最新数据（更新时间: {current_update_time}），停止爬取")
                new_tab.close()
                # 找到上次的最新数据，直接退出当前页面的循环
                break

            # 如果还没有找到上次的最新数据，则继续记录数据
            if not found_lastest or not lastest_identifier:
                # 将新数据写入CSV
                writer.writerow({
                    'page_num': page,
                    'item_index': idx + 1,
                    'ship_name': shipTxt,
                    'contact_phone': linkPhone,
                    'ship_details': shipDetailCon,
                    'image_urls': '; '.join(image_urls),  # 用分号分隔多个图片URL
                    'info_title': infoTitle,
                    'info_price': infoPrice
                })
                
                new_data_count += 1
                print(f"已添加新数据: {shipTxt}")

                # 更新进度并保存
                save_progress(page, idx + 1)

            new_tab.close()

        # 如果已经找到最新数据，退出页面循环
        if found_lastest:
            print("已找到上次的最新数据，停止爬取")
            break

        # 完成一页后重置起始索引
        start_index = 0

# 完成后删除进度文件
if os.path.exists(PROGRESS_FILE):
    os.remove(PROGRESS_FILE)

print(f"爬取完成，本次新增数据 {new_data_count} 条，保存到 {csv_filename}")