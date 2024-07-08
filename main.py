from api import *
###################
# READ SOURCE TXT #
###################

# read_source moved to ./api.py

###################
# DEFINE FEATURES #
###################

# METADATA FEATURES #


def feature_diffsize(text):
    final_ret = text
    diffsize = int(final_ret[0][0])
    fromrev_size = int(final_ret[0][9])

    if (diffsize > fromrev_size):
        return 1
    else:
        return (fromrev_size - diffsize)/fromrev_size


def feature_editcount(text):
    final_ret = text
    editcount = int(final_ret[0][1])

    # uses 12 000 edits as an arbitrary maximum
    # as of wikipedia's list of wikipedians by # of edits and wikipedia's
    # total users, this should include 99.79% of all registered users
    editcount /= 12000
    return abs(editcount)


def feature_gender(text):  # NOT USED

    final_ret = text
    gender = final_ret[0][2]
    if (gender == 'male'):
        return 1
    elif (gender == 'female'):
        return 0
    else:
        return 0.5


def feature_userage(text):
    final_ret = text
    userage = int(final_ret[0][3])

    # if user_creation date is None
    if userage == -1:
        return 0.5

    # 17000 days is approx. 46.5 years, the comparison time is 2050
    # thus only ~250 of the oldest accounts will be ignored
    # see wikipedia's database of
    # active users with the longest established accounts
    userage /= 17000
    return abs(userage)


def feature_useraccesslevel(text):
    final_ret = text
    is_anon = final_ret[0][4]
    is_autoconfirmed = final_ret[0][5]
    is_extendedconfirmed = final_ret[0][6]
    is_sysop = final_ret[0][7]

    # uses pretty arbitrary scoring system based on user privileges
    # can be further tuned for accuracy
    if (is_anon):
        return 0
    elif (is_sysop):
        return 1
    elif (is_extendedconfirmed):
        return 0.8
    elif (is_autoconfirmed):
        return 0.45


def feature_commentlength(text):
    final_ret = text
    usercomment = final_ret[0][8]
    # if has no length, return 0
    # otherwise give it a 75 char boost, then divide by 250
    # 250 chosen as an arbitrary max comment length
    if usercomment == '':
        return 0
    else:
        return abs((len(usercomment)+75)/250)


# TEXT FEATURES #


def feature_uppercase_ratio(text):
    final_ret = text
    added = final_ret[1]
    removed = final_ret[2]
    # find uppercase ratio of addition and deletion
    added_upper_ratio = uppercase_ratio(added)
    added_removed_ratio = uppercase_ratio(removed)

    # compares the ratio of upper letters in added v. removed
    return abs(added_upper_ratio - added_removed_ratio)


def feature_vulgarism(text):
    final_ret = text
    added = final_ret[1]
    removed = final_ret[2]

    added_profanity_ratio = profane_ratio(added)
    removed_profane_ratio = profane_ratio(removed)

    # compares the ratio of profanity in the added v. removed, weighted
    return abs(added_profanity_ratio - removed_profane_ratio/2)


def feature_longest_consec_char(text):
    final_ret = text
    added = final_ret[1]
    removed = final_ret[2]

    added_consec_ratio = longest_consec_char_ratio(added)
    removed_consec_ratio = longest_consec_char_ratio(removed)

    return abs(added_consec_ratio - removed_consec_ratio)


def feature_spell_err(text):
    final_ret = text
    added = final_ret[1]
    removed = final_ret[2]

    added_spell_err_ratio = spell_err_ratio(added)
    removed_spell_err_ratio = spell_err_ratio(removed)

    return abs(added_spell_err_ratio - removed_spell_err_ratio)


def feature_alpha_punct_ratio(text):
    final_ret = text
    added = final_ret[1]
    removed = final_ret[2]

    added_alpha_punct_ratio = alpha_punct_ratio(added)
    removed_alpha_punct_ratio = alpha_punct_ratio(removed)

    return abs(added_alpha_punct_ratio - removed_alpha_punct_ratio)


newFeatures = [
    feature_diffsize, feature_editcount,
    feature_userage, feature_useraccesslevel,
    feature_commentlength, feature_uppercase_ratio,
    feature_vulgarism, feature_longest_consec_char,
    feature_spell_err, feature_alpha_punct_ratio
]

print("extracting features... ")
train_feats, train_labels = get_feats_labels(load_train_data(),
                                             newFeatures=newFeatures)

print("training model... ")
model = logistic_regression()
model.train(train_feats, train_labels)

print("testing model... ")
test_feats, test_labels = get_feats_labels(load_test_data(),
                                           newFeatures=newFeatures)
print("calculating final acc... ")
pred_y = model.pred(test_feats)

acc = accuracy(pred_y, test_labels)
precision = precision_score(test_labels, pred_y)
recall = recall_score(test_labels, pred_y)
tn, fp, fn, tp = confusion_matrix(test_labels, pred_y, labels=[0, 1]).ravel()

print("final acc: " + str(acc))
print("with precision: " + str(precision) + "\nwith recall: " + str(recall))
print("with tn: " + str(tn))
print("with fp: " + str(fp))
print("with fn: " + str(fn))
print("with tp: " + str(tp))

# EOF #
