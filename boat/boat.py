import csv
import time
import json
import os

# 记录抓取进度的文件
PROGRESS_FILE = 'crawl_progress.json'
CSV_FILE = 'company_data.csv'

def load_progress():
    """加载抓取进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {'current_page': 1, 'processed_companies': 0}
    else:
        return {'current_page': 1, 'processed_companies': 0}

def save_progress(current_page, processed_companies):
    """保存抓取进度"""
    progress = {
        'current_page': current_page,
        'processed_companies': processed_companies
    }
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def init_csv_file():
    """初始化CSV文件，如果不存在则创建并写入表头"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['公司名称', '公司电话', 'QQ','手机', '联系人', '联系地址', '传真', '公司简介']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

init_csv_file()

# 加载进度
progress = load_progress()
start_page = progress['current_page']
processed_companies = progress['processed_companies']

print(f"从第{start_page}页开始抓取，已处理{processed_companies}家公司")

from DrissionPage import ChromiumPage

brower=ChromiumPage()
brower.get('https://www.crewcn.com/qiye.asp')

# 如果不是从第一页开始，需要先跳转到指定页面
if start_page > 1:
    for i in range(1, start_page):
        try:
            next_page=brower.ele('text=下一页')
            next_page.click()
            time.sleep(1)
        except Exception as e:
            print(f"跳转到第{i+1}页时出错: {e}")
            break

###翻页
for page in range(start_page, 35):
    try:
        table=brower.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[3]/table/tbody/tr/td/table[3]')
        companys=table.eles('@align=left')

        for a in companys:
            try:
                href=a.ele('tag:a').attr('href')
                tab=brower.new_tab(href)
                
                # 获取各项信息，添加容错处理
                try:
                    condition=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[1]/tbody/tr[3]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td[3]',timeout=1).text   #联系地址
                    # 去掉'联系地址：'前缀，只保留地址内容
                    if condition.startswith('联系地址：'):
                        condition = condition[4:]
                except:
                    condition = ''
                
                try:
                    conpany_name=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[1]/tbody/tr[1]/td/h1/font',timeout=0).text  ##公司名称
                except:
                    conpany_name = ''

                try:
                    conpany_phone=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[3]/tbody/tr[3]/td[4]',timeout=0).text   ##公司电话
                except:
                    conpany_phone = ''
                
                try:
                    conpany_QQ=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[3]/tbody/tr[2]/td[4]',timeout=0).text  ##QQ
                except:
                    conpany_QQ = ''
                
                try:
                    conpany_telephone=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[3]/tbody/tr[4]/td[4]',timeout=0).text    ##手机
                except:
                    conpany_telephone = ''
                
                try:
                    conpany_contract=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[3]/tbody/tr[4]/td[2]',timeout=0).text   ##联系人
                except:
                    conpany_contract = ''
                
                try:
                    company_zhen=tab.ele('x:/html/body/table/tbody/tr/td/table[4]/tbody/tr/td[1]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr/td/table[3]/tbody/tr[5]/td[4]',timeout=0).text   ##传真
                except:
                    company_zhen = ''
                
                try:
                    company_inro=tab.ele('@class=unnamed2',timeout=0).texts(text_node_only= True)[0]
                except:
                    company_inro = ''

                # 将数据写入CSV文件
                with open(CSV_FILE, 'a', newline='', encoding='utf-8-sig') as csvfile:
                    fieldnames = ['公司名称', '公司电话', 'QQ','手机', '联系人', '联系地址', '传真', '公司简介']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow({
                        '公司名称': conpany_name,
                        'QQ': conpany_QQ,
                        '公司电话': conpany_phone,
                        '手机': conpany_telephone,
                        '联系人': conpany_contract,
                        '联系地址': condition,
                        '传真': company_zhen,
                        '公司简介': company_inro
                    })
                
                b={
                        '公司名称': conpany_name,
                        'QQ': conpany_QQ,
                        '公司电话': conpany_phone,
                        '手机': conpany_telephone,
                        '联系人': conpany_contract,
                        '联系地址': condition,
                        '传真': company_zhen,
                        '公司简介': company_inro
                    }
                print(b)
                time.sleep(1)
                tab.close()
                
                # 更新并保存进度
                processed_companies += 1
                save_progress(page, processed_companies)
            except Exception as e:
                print(f"处理单个公司信息时出错: {e}")
                try:
                    tab.close()
                except:
                    pass
                continue  # 继续处理下一个公司
    except Exception as e:
        print(f"处理第{page}页时出错: {e}")
        continue  # 继续处理下一页

    try:
        next_page=brower.ele('text=下一页')
        next_page.click()
    except Exception as e:
        print(f"点击下一页按钮时出错: {e}")
        continue

# 爬取完成后删除进度文件
if os.path.exists(PROGRESS_FILE):
    os.remove(PROGRESS_FILE)
    print("爬取完成，已删除进度文件")