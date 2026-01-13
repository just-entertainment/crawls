import csv
import os
import json
from DrissionPage import ChromiumPage
from pathlib import Path

def save_progress(current_page, current_item_index):
    """保存进度"""
    progress_data = {
        'current_page': current_page,
        'current_item_index': current_item_index
    }
    with open('scraping_progress.json', 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False)

def load_progress():
    """加载进度"""
    if os.path.exists('scraping_progress.json'):
        with open('scraping_progress.json', 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
            return progress_data['current_page'], progress_data['current_item_index']
    return 1, 0

def initialize_csv():
    """初始化CSV文件，如果不存在则创建并写入表头"""
    csv_file = 'csi_employee_data.csv'
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([
                '姓名', '年龄', '籍贯', '现居住地', '毕业院校', '毕业时间', '学历', '专业',
                '特殊技能', '海龄', '现任职位', '证书等级', '外语', '婚姻', '政治面貌', '民族',
                '求职意向', '工作经历', '手机号码', '办公电话','数据来源页面'
            ])
    return csv_file

def append_to_csv(row_data, csv_file):
    """向CSV文件追加一行数据"""
    with open(csv_file, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(row_data)

# 初始化浏览器和CSV文件
browser = ChromiumPage()
csv_file_path = initialize_csv()

# 加载上次的进度
start_page, start_item_index = load_progress()
print(f"从第 {start_page} 页，第 {start_item_index} 项开始继续爬取")

##页循环
for page in range(start_page, 926):
    print(f"正在访问第 {page} 页...")
    try:
        browser.get(f'https://hr.csi.com.cn/CYJLList_{page}.html')
        table_lists = browser.ele('@class=table_list').child().children()

        # 如果是起始页，则从上次中断的位置开始
        start_idx = start_item_index if page == start_page else 0
        
        ##单页表循环
        for idx, table in enumerate(table_lists):
            # 如果是起始页且当前项索引小于起始索引，则跳过
            if page == start_page and idx < start_item_index:
                continue
                
            try:
                a_elements = table.eles('tag:a', timeout=0)
                if not a_elements:
                    continue  # 如果没有找到链接，跳过此项
                a = a_elements[0]
                href = a.attr('href')
                if f"https://hr.csi.com.cn/CYJLList_1.html" in href:
                    continue

                tab = browser.new_tab(href)

                # 获取个人信息
                infomation = tab.eles('@class=td_col2')
                
                # 安全获取个人信息，防止索引超出范围
                name = infomation[0].text if len(infomation) > 0 and hasattr(infomation[0], 'text') else ""  # 姓名
                age = infomation[1].text if len(infomation) > 1 and hasattr(infomation[1], 'text') else ""  # 年龄
                jiguan = infomation[2].text if len(infomation) > 2 and hasattr(infomation[2], 'text') else ""  # 籍贯
                xianjvzhudi = infomation[3].text if len(infomation) > 3 and hasattr(infomation[3], 'text') else ""  # 现居住地
                school = infomation[4].text if len(infomation) > 4 and hasattr(infomation[4], 'text') else ""  # 毕业院校
                time = infomation[5].text if len(infomation) > 5 and hasattr(infomation[5], 'text') else ""  # 毕业时间
                xueli = infomation[6].text if len(infomation) > 6 and hasattr(infomation[6], 'text') else ""  # 学历
                zhuanye = infomation[7].text if len(infomation) > 7 and hasattr(infomation[7], 'text') else ""  # 专业
                teshujineng = infomation[8].text if len(infomation) > 8 and hasattr(infomation[8], 'text') else ""  # 特殊技能
                hailing = infomation[9].text if len(infomation) > 9 and hasattr(infomation[9], 'text') else ""  # 海龄
                xianrenzhiwu = infomation[10].text if len(infomation) > 10 and hasattr(infomation[10], 'text') else ""  # 现任职位
                zhengshudengji = infomation[11].text if len(infomation) > 11 and hasattr(infomation[11], 'text') else ""  # 证书等级
                waiyu = infomation[12].text if len(infomation) > 12 and hasattr(infomation[12], 'text') else ""  # 外语
                hunyin = infomation[13].text if len(infomation) > 13 and hasattr(infomation[13], 'text') else ""  # 婚姻
                zhengzhimianmao = infomation[14].text if len(infomation) > 14 and hasattr(infomation[14], 'text') else ""  # 政治面貌
                minzu = infomation[15].text if len(infomation) > 15 and hasattr(infomation[15], 'text') else ""  # 民族

                # 获取求职意向和经历，使用更安全的索引访问
                table_styles = tab.eles('@class=tableStyle')
                aim = ""
                exprice = ""
                
                if len(table_styles) > 1 and hasattr(table_styles[1], 'text'):
                    aim = table_styles[1].text
                if len(table_styles) > 2 and hasattr(table_styles[2], 'text'):
                    exprice = table_styles[2].text

                # 获取手机号，使用更安全的方式
                try:
                    number_element = tab.ele('x:/html/body/form/div[5]/div[2]/div[2]/div[2]/div[1]/div/div[2]/table/tbody/tr[1]/td[4]')  ##手机
                    number_element2 = tab.ele('x:/html/body/form/div[5]/div[2]/div[2]/div[2]/div[1]/div/div[2]/table/tbody/tr[2]/td[2]') ##办公电话
                    number = number_element.text if number_element and hasattr(number_element, 'text') else ""
                    office_phone = number_element2.text if number_element2 and hasattr(number_element2, 'text') else ""
                except:
                    number = ""  # 手机

                tab.close()

                # 将数据写入CSV文件
                row_data = [
                    name, age, jiguan, xianjvzhudi, school, time, xueli, zhuanye,
                    teshujineng, hailing, xianrenzhiwu, zhengshudengji, waiyu, hunyin,
                    zhengzhimianmao, minzu, aim, exprice, number, office_phone, page
                ]
                
                append_to_csv(row_data, csv_file_path)
                print(f"已保存: {name} 的数据")

                # 保存当前进度
                save_progress(page, idx + 1)

            except Exception as e:
                print(f"处理表格项时出错: {str(e)}")
                continue

        # 当前页面处理完成后，重置起始项索引
        start_item_index = 0
        print(f"第 {page} 页处理完成")

    except Exception as e:
        print(f"访问第 {page} 页时出错: {str(e)}")
        # 发生错误时也保存进度，以便下次从中断处继续
        save_progress(page, start_item_index)
        continue

print("数据提取完成！")
browser.quit()