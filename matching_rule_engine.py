from name_match_helper import (
    dg_cv_check_is_matched_for_names,
    dg_cv_filter_employer_name,
    SC012_common_names,
    SC000_permute_matched,
    SC013_initials_check,
    SC015_word_missing,
    SC014_soundex_matched,
    RE002_initials_check,
    RE001_soundex_unequal_names,
    RE003_two_words_vs_one,
    RE005_single_name_soundex,
    RE006_name_gender_check,
    RE010_is_exact_match,
    # RE007_word_soundex
)


class MatchingRuleEngine:
    MATCHING_THRESHOLD = 0.8

    @staticmethod
    def get_name_matching_score(string_1, string_2, force_version=None):
        force_version = force_version or 2
        if force_version == 2:
            return MatchingRuleEngineV2().get_name_matching_score(string_1, string_2)
        return MatchingRuleEngineV1().get_name_matching_score(string_1, string_2)


class MatchingRuleEngineV1:
    MATCHING_THRESHOLD = 0.8

    @staticmethod
    def get_name_matching_score(string_1, string_2):
        # logger.info(f'In get_name_matching_score with [{string_1}] and [{string_2}]')

        if not all([string_1, string_2]):
            print('[ERROR] Sent blank / null strings for name matching score.')
            return None, None

        if string_1.lower() == string_2.lower():
            return True, 1.0

        is_matched, match_score = dg_cv_check_is_matched_for_names(
            dg_cv_filter_employer_name(string_1.lower()),
            dg_cv_filter_employer_name(string_2.lower())
        )
        # logger.info(f'Name Match Result: {match_score:.2} [{is_matched}]')
        return is_matched, round(match_score, 1)


def default_name_matching(name1, name2):
    return MatchingRuleEngineV1().get_name_matching_score(name1, name2)


class MatchingRuleEngineV2:
    MATCHING_THRESHOLD = 0.8

    @staticmethod
    def get_name_matching_score(string_1, string_2):

        rule_num = 0
        re_rule_num = 0
        rule_score = 0
        is_matched = False
        name_prefix = ['master', 'miss', 'mr', 'mrs', 'ms', 'w/o']

        order_list = [
            ['SC012', 'inc_common_names_missing', SC012_common_names],
            ['SC000', 'inc_permute_join_matching', SC000_permute_matched],
            ['SC013', 'inc_initials_check', SC013_initials_check],
            ['SC014', 'inc_soundex_matched', SC014_soundex_matched],
            ['SC015', '3W_2W_one_word_missing', SC015_word_missing],
            ['DEFAULT', 'default code', default_name_matching]
        ]

        reduction_list = [
            ['RE002', 'dec_initials_check', RE002_initials_check],
            ['RE001', 'dec_soundex_unequal_names', RE001_soundex_unequal_names],
            ['RE003', 'dec_two_names_vs_one', RE003_two_words_vs_one],
            ['RE005', 'dec_soundex_single_name', RE005_single_name_soundex],
            ['RE006', 'dec_name_gender_check', RE006_name_gender_check],
            ['RE010', 'dec_is_not_exact_match', RE010_is_exact_match],
            # ['RE007', 'dec_word_soundex', RE007_word_soundex]
        ]

        # logger.info(f'In get_name_matching_score of V2 with [{string_1}] and [{string_2}]')

        if not all([string_1, string_2]):
            # print('[ERROR] Sent blank / null strings for name matching score.')
            return None

        string1_replaced = string_1.lower().replace(".", " ").split()
        string2_replaced = string_2.lower().replace(".", " ").split()

        string1_replaced = [name for name in string1_replaced if name not in name_prefix]
        string2_replaced = [name for name in string2_replaced if name not in name_prefix]

        string1_replaced = ' '.join(string1_replaced)
        string2_replaced = ' '.join(string2_replaced)

        # logger.info(f'Pre-processed strings -  [{string1_replaced}] and [{string2_replaced}]')

        if not all([string1_replaced, string2_replaced]):
            # logger.error('Sent blank / null strings for name matching score.')
            return None

        if string1_replaced.lower() == string2_replaced.lower():
            return 1.0

        for rule_num in range(len(order_list)):
            is_matched, rule_score = order_list[rule_num][2](string1_replaced, string2_replaced)
            if is_matched:
                break

        # logger.info(f'Default Score after processing : {rule_score}')

        if rule_score >= 0.8 and rule_num == len(order_list) - 1 or rule_num==3:
            reduced_rule_score = rule_score
            for re_rule_num in range(0, len(reduction_list)):
                is_matched, reduced_rule_score = reduction_list[re_rule_num][2](string1_replaced,
                                                                                string2_replaced,
                                                                                rule_score)
                if reduced_rule_score < rule_score:
                    break
        else:
            reduced_rule_score = rule_score

        print(f'{order_list[rule_num][:2]} ')
        last_reached_rule = order_list[rule_num][1:2]
        if order_list[rule_num][0] == 'DEFAULT' and reduced_rule_score != rule_score:
            last_reached_rule = reduction_list[re_rule_num][1:2]
            print(f'{reduction_list[re_rule_num][:2]}')
        print(f'[{string1_replaced}] [{string2_replaced}] Result: {reduced_rule_score:.2} [{is_matched}]')
        print('*' * 100)

        return round(reduced_rule_score, 1), last_reached_rule
