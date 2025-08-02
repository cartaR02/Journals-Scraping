# journal_id,  Journal Name,    url_field,    journal_containers,     landing_page_gathering,   link_data,    headline_data,    headline_formatting_data,   date_data,    date_formatting_data,     journal_data_info,    journal_info_formatting, journal_article, article_tag, abstract,    load_time,    bypass,   status
# article tag is the "type" of article it is whether is says Research, Article, but to filter out ones that say "Introduction" Correction ,Errata etc...
psycnet_line = ",,,find|class|volume-wrapper~find_all|elem|li,True,find|elem|a,find|elem|a,,find_all|elem|span|1|2,swap,find|class|list,,5,True,D"
sagepub_line = ",,,find|class|loi__issues~find_all|class|loi__issue,True,find|elem|a,find|elem|a,,find|class|loi__issue__cover-date,,find|class|table-of-content,,,,D"

def assign_csv_line(journal_domain):
    if "psycnet" in journal_domain:
        return psycnet_line.split(",")
    elif "sagepub" in journal_domain:
        return sagepub_line.split(",")
