import requests
import json


ajax_url = 'http://www.topshop.com/webapp/wcs/stores/servlet/CatalogNavigationAjaxSearchResultCmd?storeId=12556&catalogId=33057&langId=-1&dimSelected=/en/tsuk/category/new-in-this-week-2169932/new-in-fashion-6367514/N-8d7Zdgl?No=0&Nrpp=1000&siteId=/12556&categoryId=277012'

ajax_req = requests.get(ajax_url)

# print(ajax_req.url)

json_dict = json.loads(ajax_req.text)

results = json_dict['results']

contents = results['contents'][0]

total_nr_recs = contents['totalNumRecs']

pages = int(total_nr_recs/20) + 1

loop_count = pages

counter = 0

i = 0
while i < loop_count:
    ajax_url = 'http://www.topshop.com/webapp/wcs/stores/servlet/CatalogNavigationAjaxSearchResultCmd?storeId=12556&catalogId=33057&langId=-1&dimSelected=/en/tsuk/category/new-in-this-week-2169932/new-in-fashion-6367514/N-8d7Zdgl?No=' + str(i*20) + '&Nrpp=20&siteId=/12556&categoryId=277012'
    i += 1

    ajax_req = requests.get(ajax_url)

    # print(ajax_req.url)

    json_dict = json.loads(ajax_req.text)

    results = json_dict['results']

    contents = results['contents'][0]

    records = contents['records']

    for record in records:
        product_url = 'http://www.topshop.com' + record['productUrl']
        print(product_url)
        counter += 1

print(counter)