# journal_id,  Journal Name,    url_field,    journal_containers,     landing_page_gathering,   link_data,    headline_data,    headline_formatting_data,   date_data,    date_formatting_data,     journal_data_info,    journal_info_formatting, journal_articles, phrase_tag, abstract,    load_time,    bypass,   status
# article tag is the "type" of article it is whether is says Research, Article, but to filter out ones that say "Introduction" Correction ,Errata etc...
psycnet_line = ",,,find|class|volume-wrapper~find_all|elem|li,True,find|elem|a,find|elem|a,,find_all|elem|span|1|2,swap,find|class|list,,5,True,D"
sagepub_line = ",,,find|class|loi__issues~find_all|class|loi__issue,True,find|elem|a,find|elem|a,,find|class|loi__issue__cover-date,,find|class|table-of-content,,find_all|class|issue-item__container ,find|class|issue-item__header~find_all|elem|span|2,find|elem|a,find_all|class|core-container|3~find|elem|div,5,,D"
lww_line = ",,,find|class|loi__issues~find_all|class|loi__issue,True,find|elem|a,find|elem|a,,find|class|loi__issue__cover-date,,find|class|table-of-content,,find_all|class|issue-item__container ,find|class|issue-item__header~find_all|elem|span|2,find|elem|a,find_all|class|core-container|3~find|elem|div,5,,D"

# saving this
# 30179,Journal of Educational Psychology,https://psycnet.apa.org/PsycARTICLES/journal/edu/117/4|https://psycnet.apa.org
# 30639,Diversity in Higher Education,https://psycnet.apa.org/PsycARTICLES/journal/dhe/18/3|https://psycnet.apa.org
# 30639,Diversity in Higher Education,https://psycnet.apa.org/PsycARTICLES/journal/dhe/18/3|https://psycnet.apa.org
# 33518,School Psychology,https://psycnet.apa.org/PsycARTICLES/journal/spq/40/1|https://psycnet.apa.org
def assign_csv_line(journal_domain):
    domain_map = {
        "psycnet": psycnet_line,
        # not worrying about sage pub
        "sagepub": sagepub_line,
        "lww": lww_line
    }

    for keyword, line in domain_map.items():
        if keyword in journal_domain:
            return line.split(",")
    return None