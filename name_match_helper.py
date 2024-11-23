from fuzzywuzzy import fuzz
from py4Soundex.code import Soundex

common_surnames = ['bhai', 'kumar', 'rao', 'das', 'lal', 'iyer']


def check_input_name_in_website_name(name_1, name_2):
    list_name_split_by_space = name_1.split()

    is_all_words_matching = True 
    for word_in_name in list_name_split_by_space:
        if word_in_name not in name_2:
            is_all_words_matching = False
            break

    return is_all_words_matching


def get_unmatched_single_char_scoring(input_unmatched_words, unmatched_words):
    """
    Calculating score for sort names
    e.g. like 'Raj Kapoor and Raj k' or  'Vishwa k and Vishwa Kumar'

    :param input_unmatched_words:
    :param unmatched_words:
    :return:
    """
    try:
        # here min 1 unmatch will come
        input_unmatched_words.sort()
        # this below one "unmatched_words" is response subtract input
        unmatched_words.sort()

        single_char_matched_count = 0
        for k, v in enumerate(input_unmatched_words):
            try:
                if (v == unmatched_words[k][0]) or (unmatched_words[k] == v[0]):
                    single_char_matched_count += 1
            except:
                pass

        if single_char_matched_count == len(input_unmatched_words):
            return 90
        if single_char_matched_count == 0:
            score_output = 40
        else:
            score_output = 80
        return score_output
    except Exception as err:
        print(f"Exception Error in get_unmatched_single_char_scoring : {err}")
    return 0


def process_matched_name_with_first_letter_match(input_name, emp_name):
    score_output = 0
    input_request_list = input_name.split(" ")
    resp_list = emp_name.split(" ")

    # this is for calculating initials if name containing single chars
    unmatched_words = list(set(resp_list) - set(input_request_list))
    input_unmatched_words = list(set(input_request_list) - set(resp_list))
    unmatched_words.sort()
    input_unmatched_words.sort()

    if len(unmatched_words) == len(input_unmatched_words):
        if len(input_unmatched_words) > 0:
            single_char_scoring = get_unmatched_single_char_scoring(input_unmatched_words, unmatched_words)
            # if this single_char_scoring is >=90 then only we want this score
            # otherwise whatever score we got from "calculating_score" is fine
            if single_char_scoring > 80:
                score_output = single_char_scoring
            else:
                score_output = 40
        else:
            # No unmatched words
            score_output = 90

    return score_output


def dg_cv_check_is_matched_for_names(input_name, dg_response_name, allow_retry=True):
    is_matched = False
    sort_ratio = fuzz.token_sort_ratio(input_name, dg_response_name)
    set_ratio = fuzz.token_set_ratio(input_name, dg_response_name)
    temp_score = (sort_ratio + set_ratio) / 2

    base_score = 41

    # if the (sort ratio + set ratio) // 2 is greater than 80 then check match with the first letter
    if temp_score > 80:
        score_output = process_matched_name_with_first_letter_match(
            str(input_name).lower(), str(dg_response_name).lower())

        if score_output == 40 and temp_score < 95:
            update_score = (base_score + temp_score) // 2
            temp_score = update_score

    # after filtering out the input name, there should be something in the company name
    if input_name:
        if temp_score > 80 or dg_response_name.startswith(input_name) or input_name.startswith(dg_response_name):
            is_matched = True

    match_score = round(temp_score / 100, 2)
    # logger.info(f'Default Name Match Score [{match_score}] for [{input_name}] and [{dg_response_name}]')

    if not is_matched and match_score < 0.8 and allow_retry:
        is_matched, match_score = dg_cv_check_is_matched_for_names(
            input_name.replace(' ', ''),
            dg_response_name.replace(' ', ''),
            False
        )

    if match_score == 1:
        total_num_of_spaces = (input_name.count(' ') + dg_response_name.count(' ')) or 0.256
        space_weight = 0.2 * (input_name.count(' ') / total_num_of_spaces)
        match_score -= space_weight

    return is_matched, round(match_score, 2)


def dg_cv_filter_employer_name(company_name):
    prefix_names = ['limited', 'ltd', 'ltd.', 'private', 'pvt', 'pvt.', 'co', 'co.', 'company', 'pvt.ltd']

    company_name_list = company_name.split(" ")

    for common_name in prefix_names:
        if common_name in company_name_list:
            company_name = str(company_name).replace(common_name, "").strip()

    # logger.info("company_name after filter_employer_name ")
    # logger.info(company_name)

    return company_name.strip()


def SC000_permute_matched(input_name, dg_response_name):
    """
    calculate score for joined but same names
    e.g. "Jakeerhussain Shaik" and "SHAIK JAKEER HUSSAIN"
    """
    try:
        # logger.info("Inside SC000_permute_matched")
        is_matched = False
        score_output = 0.0

        name1 = input_name
        name2 = dg_response_name

        name1_list = input_name.split(" ")
        name2_list = dg_response_name.split(" ")

        lhs = [x for x in name1_list if x]
        rhs = [x for x in name2_list if x]

        if not len(lhs) - len(rhs):
            return is_matched, score_output

        if len(rhs) > len(lhs):
            lhs = name2_list
            rhs = name1_list
            name1 = (' '.join(lhs))
            name2 = (' '.join(rhs))

        for i in range(0, len(lhs)):
            if name2.find(lhs[i]) != -1:
                name2 = name2.replace(lhs[i], "")
                name1 = name1.replace(lhs[i], "")

        if name2.isspace() and name1.isspace():
            is_matched = True
            score_output = 0.8

        return is_matched, score_output

    except Exception as err:
        print(f"Exception happens while score calculation and error is : {err}")


def SC015_word_missing(input_name, dg_response_name):
    """
    Used for cases where 3 word string and 2 word string for match
       e.g.  "Archana Bholaram Gupta"  and "Archana Gupta"
    """
    try:
        is_matched = False
        score_output = 0

        name1_list = input_name.split(" ")
        name2_list = dg_response_name.split(" ")

        if not ((len(name1_list) == 3 and len(name2_list) == 2) or
                (len(name1_list) == 2 and len(name2_list) == 3)):
            return is_matched, score_output
        if any(len(item) == 1 for item in (name1_list + name2_list)):
            return is_matched, score_output

        no_match_1 = list(set(name1_list) - set(name2_list))
        no_match_2 = list(set(name2_list) - set(name1_list))
        if ((len(no_match_1) == 1) and not len(no_match_2) or
                (len(no_match_2) == 1 and not len(no_match_1))):
            score_output = 0.8
            is_matched = True
        return is_matched, score_output
    except Exception as err:
        print(f"Exception occurs while calculating the score. Error: {err}")


def SC012_common_names(input_name, dg_response_name):
    """
    calculate score for names with common surnames
    common_names like "bhai", "kumar", "rao"
    eg . "Tushar Parmar" and "Parmar Tusharbhai"
    """
    try:
        # logger.info("Inside SC012_common_names")
        is_matched = False
        score_output = 0.0

        name1_list = input_name.split(" ")
        name2_list = dg_response_name.split(" ")

        if len(name2_list) != len(name1_list):
            return is_matched, score_output

        for i in common_surnames:
            if input_name.count(i) - dg_response_name.count(i):
                is_matched, score_output = compare_name(name1_list, name2_list, i)

        return is_matched, score_output

    except Exception as err:
        print(f"Exception happens while score calculation and error is : {err}")


def compare_name(name1_list, name2_list, common_name):
    name1_sorted_list = sorted(name1_list)
    name2_sorted_list = sorted(name2_list)
    is_same = False
    for i in range(0, len(name1_sorted_list)):
        if name1_sorted_list[i] == name2_sorted_list[i]:
            is_same = True
        elif (name1_sorted_list[i] + common_name == name2_sorted_list[i]
              or name2_sorted_list[i] + common_name == name1_sorted_list[i]):
            is_same = True
        else:
            is_same = False
            return is_same, 0.0

    return is_same, 0.8


def SC013_initials_check(input_name, dg_response_name):
    """
    """
    try:
        # logger.info("Inside SC013_initials_check")
        is_matched = False
        score_output = 0.0

        name1_list = input_name.split(" ")
        name2_list = dg_response_name.split(" ")

        no_match_1 = list(set(name1_list) - set(name2_list))
        no_match_2 = list(set(name2_list) - set(name1_list))

        if len(no_match_1) != len(no_match_2):
            return is_matched, score_output

        if set(no_match_1) == set(name1_list) or set(no_match_2) == set(name2_list):
            return is_matched, score_output

        match_count = 0
        mismatched = 0
        for ele in no_match_1:
            for name in no_match_2:
                if ele[0] == name[0] and (len(ele) == 1 or len(name) == 1):
                    match_count += 1
                    is_matched = True
                else:
                    mismatched += 1
                    is_matched = False
        if match_count == 1 and mismatched == 0:
            score_output = 0.9
        elif match_count >= 2 and mismatched == 0:
            score_output = 0.8

        return is_matched, score_output

    except Exception as err:
        print(f"Exception happens while score calculation and error is : {err}")


def SC014_soundex_matched(input_name, dg_response_name):
    """
    Michael RAMKUMAR - Micheal Ramkumar  -> 0.8
    """
    try:
        # logger.info("Inside SC014_soundex_matched")
        is_matched = False
        score_output = 0.0

        name1_list = input_name.split(" ")
        name2_list = dg_response_name.split(" ")

        if len(name1_list) != len(name2_list):
            return is_matched, score_output

        no_match_1 = list(set(name1_list) - set(name2_list))
        no_match_2 = list(set(name2_list) - set(name1_list))

        if (len(no_match_1) != len(no_match_2)) or (not len(no_match_1) and not len(no_match_2)):
            return is_matched, score_output

        if set(no_match_1) == set(name1_list) or set(no_match_2) == set(name2_list):
            # confirms no matching strings
            return is_matched, score_output

        try:
            joined_name1 = ''.join(sorted(no_match_1))
            joined_name2 = ''.join(sorted(no_match_2))
            if joined_name1 not in joined_name2 and joined_name2 not in joined_name1:
                if Soundex(joined_name1) == Soundex(joined_name2):
                    is_matched = True
                    score_output = 0.8
        except:
            pass
        return is_matched, score_output

    except Exception as err:
        print(f"Exception happens while score calculation and error is : {err}")


def RE001_soundex_unequal_names(input_name, dg_response_name, score_output):
    # logger.info("Inside RE001_soundex_unequal_names")
    is_matched = True

    name1_list = input_name.split(" ")
    name2_list = dg_response_name.split(" ")

    if len(name2_list) != len(name1_list):
        return is_matched, score_output

    no_match_1 = list(set(name1_list) - set(name2_list))
    no_match_2 = list(set(name2_list) - set(name1_list))

    full_list1 = no_match_2 + no_match_1
    full_list2 = [x for x in full_list1 if len(x)]

    if not len(full_list2) or full_list2 != full_list1:
        return is_matched, score_output

    if set(no_match_1) == set(name1_list) or len(no_match_2) != len(no_match_1):
        # check if there is common names in name1_list and name2_list
        return is_matched, score_output

    if len(no_match_1) > 1 or no_match_1[0][0] != no_match_2[0][0]:
        is_matched = False
        score_output -= 0.2
        return is_matched, score_output

    try:
        if Soundex(no_match_1[0]) != Soundex(no_match_2[0]):
            is_matched = False
            score_output -= 0.1
    except:
        pass

    return is_matched, score_output


def RE002_initials_check(input_name, dg_response_name, score_output):
    # logger.info("Inside RE002_initial_check")
    is_matched = True
    match_count = 0

    name1_list = input_name.split(" ")
    name2_list = dg_response_name.split(" ")

    no_match_1 = list(set(name1_list) - set(name2_list))
    no_match_2 = list(set(name2_list) - set(name1_list))

    if not (len(no_match_1) or len(no_match_2)):
        # confirms if all strings are matching
        return is_matched, score_output

    if set(name1_list) == set(no_match_1) or set(name2_list) == set(no_match_2):
        # confirms NO matching string in names
        return is_matched, score_output

    if len(name1_list) >= 3 or len(name2_list) >= 3:
        if len(name1_list) > len(name2_list) or len(name2_list) > len(name1_list):
            is_matched = False
            score_output = 0.7
            return is_matched, score_output

    matched_string = len(name1_list) - len(no_match_1)
    unmatched_string = len(no_match_1) if len(no_match_1) > len(no_match_2) else len(no_match_1)

    if (len(no_match_1) and not len(no_match_2)) or (len(no_match_2) and not len(no_match_1)):
        # Confirms extra letter or word after removing matching names
        score_output = 0.7 if matched_string >= 2 else 0.8
        return is_matched, score_output

    for ele in no_match_1:
        for word in no_match_2:
            if ele[0] == word[0]:
                match_count += 1
    if not match_count:
        score_output = 0.7

    return is_matched, score_output


def RE003_two_words_vs_one(input_name, dg_response_name, score_output):
    # logger.info("Inside RE003_two_words_vs_one")
    is_matched = True

    name1_list = input_name.split(" ")
    name2_list = dg_response_name.split(" ")

    if len(name2_list) == len(name1_list):
        return is_matched, score_output

    full_list1 = name1_list + name2_list
    full_list2 = [x for x in full_list1 if len(x) > 1]

    if not len(full_list2) or full_list2 != full_list1:
        return is_matched, score_output

    joined_name1 = ''.join(name1_list)
    joined_name2 = ''.join(name2_list)

    try:
        if Soundex(joined_name1) != Soundex(joined_name2):
            is_matched = False
            score_output -= 0.1
    except:
        pass
    return is_matched, score_output


def RE005_single_name_soundex(input_name, dg_response_name, score_output):
    # logger.info("Inside RE005_single_name_soundex")
    is_matched = True

    name1_list = input_name.split(" ")
    name2_list = dg_response_name.split(" ")

    rm_initial_name1 = [x for x in name1_list if len(x) > 1]
    rm_initial_name2 = [x for x in name2_list if len(x) > 1]

    if len(rm_initial_name1) > 1 or len(rm_initial_name2) > 1:
        return is_matched, score_output

    try:
        if Soundex(rm_initial_name1[0]) != Soundex(rm_initial_name2[0]):
            is_matched = False
            score_output -= 0.1
    except:
        pass

    return is_matched, score_output


def RE006_name_gender_check(input_name, dg_response_name, score_output):
    """
    Checks Name
    'Praveen' and 'Praveena' -> Default - 0.3
    'Selva kumar' and 'Selva kumari' -> Default - 0.3
    'RamaKrishna' and 'Ramakrishnaa' -> Default
    """
    # logger.info("Inside RE006_name_gender_check")
    is_matched = True

    name1_list = input_name.split(" ")
    name2_list = dg_response_name.split(" ")

    no_match_1 = list(set(name1_list) - set(name2_list))
    no_match_2 = list(set(name2_list) - set(name1_list))

    for string in no_match_1:
        for obj in no_match_2:
            if obj.count(string):
                if obj.replace(string, '') in ['a', 'i'] and obj[-2:-1] not in ['a']:
                    is_matched = False
                    score_output -= 0.3
            elif string.count(obj):
                if string.replace(obj, '') in ['a', 'i'] and string[-2:-1] not in ['a']:
                    is_matched = False
                    score_output -= 0.3

    return is_matched, score_output


def RE010_is_exact_match(input_name, dg_response_name, score_output):
    # logger.info("Inside RE010_is_exact_match")
    is_matched = True
    non_match = 0

    if score_output != 1.0:
        return is_matched, score_output

    name1_list = input_name.split(" ")
    name2_list = dg_response_name.split(" ")

    no_match_1 = list(set(name1_list) - set(name2_list))
    no_match_2 = list(set(name2_list) - set(name1_list))

    if len(no_match_1) == len(no_match_2):
        for i in range(len(name1_list)):
            if name2_list[i][:1] != name1_list[i][:1]:
                non_match += 1
    if non_match:
        score_output -= 0.2
        return is_matched, score_output

    if no_match_1 != no_match_2:
        score_output -= 0.1

    return is_matched, score_output


# def RE007_word_soundex(input_name, dg_response_name, score_output):
#     is_matched = True
#
#     name1_list = input_name.split(" ")
#     name2_list = dg_response_name.split(" ")
#
#     no_match_1 = list(set(name1_list) - set(name2_list))
#     no_match_2 = list(set(name2_list) - set(name1_list))
#
#     if len(no_match_1) != len(no_match_2):
#         return is_matched, score_output
#
#     non_match_count = 0
#     for word1, word2 in zip(no_match_1, no_match_2):
#         if len(word1) > 3 and len(word2) > 3:
#             if Soundex(word1) != Soundex(word2):
#                 non_match_count += 1
#
#     if non_match_count == len(no_match_1):
#         is_matched = False
#         score_output -= 0.2
#     elif non_match_count > 0:
#         is_matched = False
#         score_output -= 0.1
#
#     return is_matched, score_output






