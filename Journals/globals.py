# used for lede formatting
month = [
    "zero",
    "Jan.",
    "Feb.",
    "March",
    "April",
    "May",
    "June",
    "July",
    "Aug.",
    "Sept.",
    "Oct.",
    "Nov.",
    "Dec.",
]
# trying to avoid specific sites keyword skips but using some here as just a global check
# searches through description
keyword_skips = ["PRNewswire", "Desarrollo Economico", "Asociacion Americana", "Gouvernement", "GLOBE NEWSWIRE", "Nueva", "Congreso", "BUSINESS WIRE", "sex", "Sex"]

# number of invalid dates until web skip
invalid_dates: int = 4

# id chosen to be tested
single_id: int = 0


# number of urls processed
url_count: int = 0

# Possible error that fails to access website
failed_access: list[str] = []

# Failed access for 403 error only
failed_access_403: list[str] = []

# error for when no links are gathered
no_links: list[str] = []

# list for when checkign titles and date size
no_titles: list[str] = []


# list to print out element scrape errors
element_not_found: list[str] = []


##############################################################################
# invalid load time field x
invalid_load_time: list[str] = []

# x means its added to the main
# errors
# skipping with no lede x
no_uname_found: list[str] = []

# skipping with no lede x
no_lead_found: list[str] = []

# unable to create filename x
filename_creation_error: list[str] = []

# getting filename returns none  x
filename_is_none: list[str] = []

# landing page giving a none value x
# when trying to find the href of the landing page
article_link_href_typeerror_none: list[str] = []

# description is none or len is none x
article_description_is_none: list[str] = []

# articles that were skipped due to a key word
# log them so we know x
article_skipped_keyword_found: list[str] = []

# when retriving initiall html this is the list of erros
landing_page_html_is_none: list[str] = []

# tried to get containers for landing page
landing_page_containers_html_is_none: list[str] = []

# checks for links==dates==titles amounts
unequal_titles_dates_links_counts: list[str] = []

# none objects for titles, dates, links
date_is_none: list[str] = []

title_is_none: list[str] = []

link_is_none: list[str] = []

# cloud scraper errors
cloud_scrapper_error: list[str] = []

# could be list of int but just easier
csv_line_error: list[str] = []

# issues when adding to database usually relating to stray ascii characters
sql_insert_error: list[str] = []

##### DOC LINES

# succesffully added docs x
successfully_added_doc: list[str] = []

# number of duplicates in the given pull x
duplicate_docs: list[str] = []

# certain character limit set for size x
char_limit_to_skip: int = 100
article_description_too_short: list[str] = []

# list for rejected docs that failed to gather data
# valid docs there but just not gathered
rejected_docs: list[str] = []

# paralell eachother to show what string to print along with it
error_list_wrapper: list[list] = []
error_list_string_wrapper: list[str] = []

doc_list_wrapper: list[list] = []
doc_list_string_wrapper: list[str] = []
# crazy ahh appends
# TODO still gotta add a sring list that parallels the list here so i can add what words go along with the error logss
error_list_wrapper.append(invalid_load_time)
error_list_wrapper.append(no_uname_found)
error_list_wrapper.append(no_lead_found)
error_list_wrapper.append(filename_creation_error)
error_list_wrapper.append(filename_is_none)
error_list_wrapper.append(article_link_href_typeerror_none)
error_list_wrapper.append(article_description_is_none)
error_list_wrapper.append(article_skipped_keyword_found)
error_list_wrapper.append(landing_page_html_is_none)
error_list_wrapper.append(landing_page_containers_html_is_none)
error_list_wrapper.append(unequal_titles_dates_links_counts)
error_list_wrapper.append(date_is_none)
error_list_wrapper.append(title_is_none)
error_list_wrapper.append(link_is_none)
error_list_wrapper.append(cloud_scrapper_error)
error_list_wrapper.append(csv_line_error)
error_list_wrapper.append(sql_insert_error)
error_list_wrapper.append(successfully_added_doc)
error_list_wrapper.append(duplicate_docs)
error_list_wrapper.append(article_description_too_short)
error_list_wrapper.append(rejected_docs)

invalid_load_time_str = "Invalid Load Times:"
no_uname_found_str = "No UNAME Found:"
no_lead_found_str = "No Lede Found:"
filename_creation_error_str = "Filename Creation Error:"
filename_is_none_str = "Filename Is None:"
article_link_href_typeerror_none_str = "Article Link href Failed to Grab:"
article_description_is_none_str = "Article Description is None:"
article_skipped_keyword_found_str = "Article Skipped Due to Keyword:"
landing_page_html_is_none_str = "Landing Page HTML is None:"
landing_page_containers_html_is_none_str = "Landing Page Containers HTML is None:"
unequal_titles_dates_links_counts_str = "Landing Page Counts for Titles, Dates, Links Do Not Equal:"
date_is_none_str = "Date Found NoneType:"
title_is_none_str = "Title Found NoneType:"
link_is_none_str = "Link Found NoneType:"
cloud_scrapper_error_str = "Cloud Scraper Failed to Resolve:"
csv_line_error_str = "CSV Line Has Improper Setup:"
sql_insert_error_str = "Error Inserting into Database:"
rejected_docs_str = "Rejected Docs:"

error_list_string_wrapper.append(invalid_load_time_str)
error_list_string_wrapper.append(no_uname_found_str)
error_list_string_wrapper.append(no_lead_found_str)
error_list_string_wrapper.append(filename_creation_error_str)
error_list_string_wrapper.append(filename_is_none_str)
error_list_string_wrapper.append(article_link_href_typeerror_none_str)
error_list_string_wrapper.append(article_description_is_none_str)
error_list_string_wrapper.append(article_skipped_keyword_found_str)
error_list_string_wrapper.append(landing_page_html_is_none_str)
error_list_string_wrapper.append(landing_page_containers_html_is_none_str)
error_list_string_wrapper.append(unequal_titles_dates_links_counts_str)
error_list_string_wrapper.append(date_is_none_str)
error_list_string_wrapper.append(title_is_none_str)
error_list_string_wrapper.append(link_is_none_str)
error_list_string_wrapper.append(cloud_scrapper_error_str)
error_list_string_wrapper.append(csv_line_error_str)
error_list_string_wrapper.append(sql_insert_error_str)
error_list_string_wrapper.append(rejected_docs_str)

## docs

doc_list_wrapper.append(successfully_added_doc)
doc_list_wrapper.append(duplicate_docs)
doc_list_wrapper.append(article_description_too_short)

successfully_added_doc_str = "Loaded:"
duplicate_docs_str = "Duplicates:"
article_description_too_short_str = "Article Description Too Short:"

doc_list_string_wrapper.append(successfully_added_doc_str)
doc_list_string_wrapper.append(duplicate_docs_str)
doc_list_string_wrapper.append(article_description_too_short_str)