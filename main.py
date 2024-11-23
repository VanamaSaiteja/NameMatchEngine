from matching_rule_engine import MatchingRuleEngine

if __name__ == '__main__':
    # str1 = 'shruti singh shekhawat'
    # str2 = 'shruthy s shekhawat'
    #  str1 = 'rajdeep kalra'
    #  str2 = 'pradeep kumar'
    #  str1 = 'gupta raju'
    #  str2 = 'gupta rakesh'
    str1 = 'Sravan Kumar'
    str2 = 'Saravana Kumar'

#     v1_score = MatchingRuleEngine().get_name_matching_score(str1, str2, 1)
    v2_score = MatchingRuleEngine().get_name_matching_score(str1, str2, 2)
#     print(f"V1 Score: {v1_score}")
    print(f'Name1 : {str1} | Name2 : {str2} | Score: {v2_score}')
# import pandas as pd
# from matching_rule_engine import MatchingRuleEngine

# def process_excel(file_path):
#     df = pd.read_excel(file_path)
#     if not {'name1', 'name2', 'function'}.issubset(df.columns):
#         raise ValueError("Excel file must contain 'name1', 'name2', and 'function' columns")
#     engine = MatchingRuleEngine()
#     for index, row in df.iterrows():
#         name1 = row['name1']
#         name2 = row['name2']
#         function_name = row['function']
#         if function_name == 'inc_permute_join_matching':
#             score = engine.get_name_matching_score(name1, name2, 2)  
#         else:
#             score = 0.0 
#         print(f"Name1: {name1} | Name2: {name2} | Function: {function_name} | Calculated Score: {score}")

# if __name__ == '__main__':
#     path = 'C:/Users/saiteja/Desktop/testcs.xlsx'
#     process_excel(path)
