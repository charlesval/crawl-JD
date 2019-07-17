import requests
from bs4 import BeautifulSoup
import re, json
from urllib import parse
import threadpool


"""
https://search.jd.com/Search?keyword=T%E6%81%A4%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=T%E6%81%A4%E7%94%B7&page=1&s=1&click=0
https://search.jd.com/Search?keyword=T%E6%81%A4%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=T%E6%81%A4%E7%94%B7&page=3&s=52&click=0
https://search.jd.com/Search?keyword=T%E6%81%A4%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=T%E6%81%A4%E7%94%B7&page=5&s=101&click=0
https://search.jd.com/Search?keyword=T%E6%81%A4%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=T%E6%81%A4%E7%94%B7&page=7&s=152&click=0
https://search.jd.com/Search?keyword=T%E6%81%A4%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=T%E6%81%A4%E7%94%B7&page=9&s=222&click=0
"""

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
base = 'https://item.jd.com'

def write_csv(row):
    with open('shop.txt',"a+",encoding='utf8')as f:
        f.write(row)

def get_id(url):
    id = re.compile('\d+')
    res = id.findall(url)
    return res[0]

def get_comm(url,comm_num):
    good_comments=[]#存放结果
    #获取评论
    item_id = get_id(url)
    pages=comm_num//10
    error_num=0#定义请求失败次数
    for page in range(pages):
        if error_num>2:
            return good_comments
        comment_url = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv113&productId={}&score=0&sortType=5&page={}&pageSize=10&isShadowSku=0&fold=1'.format(
            item_id,page)
        headers['Referer'] = url
        comment = requests.get(comment_url, headers=headers).text
        start = comment.find('{"productAttr"')
        end = comment.find('"afterDays":0}]}') + len('"afterDays":0}]}')
        try:
            content = json.loads(comment[start:end])
            comments = content['comments']
            for c in comments:
                comm=c['content']
                good_comments.append(comm)
        except:
            error_num+=1
            continue
    return good_comments

def get_comm_num(url):
    #获取评论数量
    item_id=get_id(url)
    comm_url='https://club.jd.com/comment/productCommentSummaries.action?referenceIds={}&callback=jQuery7016680'.format(item_id)
    comment = requests.get(comm_url, headers=headers).text
    start=comment.find('{"CommentsCount"')
    end=comment.find('"PoorRateStyle":0}]}')+len('"PoorRateStyle":0}]}')
    try:
        content=json.loads(comment[start:end])['CommentsCount']
    except:
        content=None
        return 0
    comm_num=content[0]['CommentCount']
    return comm_num

def get_shop_info(url):
    shop_data={}
    html=requests.get(url,headers=headers)
    soup=BeautifulSoup(html.text,'lxml')
    shop_name=soup.select(".popbox-inner .mt h3 a")[0].text
    shop_score=soup.select(".score-part span.score-detail em")
    try:
        shop_evaluation=shop_score[0].text
        logistics=shop_score[1].text
        sale_server=shop_score[2].text
    except:
        shop_evaluation=None
        logistics=None
        sale_server=None
    shop_info=soup.select("div.p-parameter ul")
    shop_brand=shop_info[0].select("ul li a")[0].text
    try:
        shop_other=shop_info[1].select('li')
        for s in shop_other:
            data=s.text.split('：')
            key=data[0]
            value=data[1]
            shop_data[key]=value
    except:
        shop_other=None
    shop_data['shop_name']=shop_name
    shop_data['shop_evaluation']=shop_evaluation
    shop_data['logistics']=logistics
    shop_data['sale_server']=sale_server
    shop_data['shop_brand']=shop_brand
    return shop_data


def get_index(page, s):

    #建立线程对象
    #index_thread=ThreadPoolExecutor()
    #一开始的请求页面
    url = 'https://search.jd.com/Search?keyword=T%E6%81%A4%E7%94%B7&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=T%E6%81%A4%E7%94%B7&' \
          'page={}&s={}&click=0'.format(page, s)
    html = requests.get(url, headers=headers)
    soup = BeautifulSoup(html.text, 'lxml')
    items = soup.select('li.gl-item')
    for item in items:
        #index_thread.submit(get_index_thread,item=item,filename=filename)
        inner_url = item.select('.gl-i-wrap div.p-img a')[0].get('href')
        inner_url = parse.urljoin(base, inner_url)
        # 价格
        price = item.select("div.p-price strong i")[0].text
        #评论数
        comm_num=get_comm_num(inner_url)
        #店铺内部信息
        shop_info_data=get_shop_info(inner_url)
        #获取评论
        comments=None
        if comm_num>0:
            comments=get_comm(inner_url,comm_num)

        shop_info_data['comments']=comments
        shop_info_data['price']=price
        shop_info_data['comm_num']=comm_num

        print(shop_info_data)
        shop_info_data=str(shop_info_data)+'\n'
        write_csv(shop_info_data)


if __name__ == '__main__':
    vars=[]
    pool=threadpool.ThreadPool(10)
    s = 1
    for i in range(1, 200, 2):
        vars.append(([i,s],None))
        s = s + 51
    print(vars)
    reque=threadpool.makeRequests(get_index,vars)
    for r in reque:
        pool.putRequest(r)
    pool.wait()
