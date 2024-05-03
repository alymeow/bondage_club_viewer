import simplejson as json

ignore_activates = ['ChatSelf-ItemButt-BCAR_TailWag']
ignore_actions = ['ServerUpdateRoom', 'ActionRemove', 'ServerMoveLeft', 'ServerSwap', 'ChangeClothes',
                  'ActionChangeColor',
                  'ActionLoosenStruggle', 'ArmsRopeSetHogtied', 'ActionLoosenLot', 'ServerBan', 'SlowLeaveCancel',
                  'ActionDismount',
                  'TextItemChange',
                  ]


def convert_item(item) -> str:
    if item == 'Feather':
        return '羽毛'
    elif 'ItemMouth' in item:
        return '嘴巴'
    elif item == 'ItemHandheld':
        return '手'
    elif item == 'ItemHand':
        return '手'
    elif item == 'ItemArms':
        return '手臂'
    elif item == 'ItemNeckRestraints':
        return '脖颈'
    elif item == 'ItemVulva':
        return '阴部'
    elif item == 'ItemNipples':
        return '乳头'
    elif item == 'ItemFeet':
        return '脚'
    elif item == 'ItemLegs':
        return '腿'
    elif item == 'ItemBoots':
        return '鞋'
    elif item == 'ItemDevices':
        return '身体'
    elif item == 'ItemHead':
        return '头'
    elif item == 'Whip':
        return '鞭子'
    elif item == 'ItemEar':
        return '耳朵'
    elif item == 'ItemButt':
        return '屁股'
    else:
        # print("unknown item:", item)
        return item


def dictionary_get(dictionary, tag, key='Text'):
    # print('d1: tag={}, key={}, dict={}'.format(tag, key, dictionary))
    for ele in dictionary:
        if ele.get('Tag') == tag:
            if key == 'AssetName' and ele.get('CraftName') != None:
                return ele['CraftName']
            elif key == 'FocusGroupName' and ele.get('FocusGroupName') != None:
                return convert_item(ele[key])
            elif key == 'FocusGroupName' and ele.get('AssetGroupName') != None:
                return convert_item(ele['AssetGroupName'])
            else:
                # print('d2: key={}, ele={}'.format(key, ele))
                if ele.get(key):
                    return convert_item(ele[key])
                else:
                    return ""
    return None


def characters_get(element) -> tuple:
    src = None
    tgt = None
    if element.get('characters') is None:
        return None, None

    characters = element['characters']
    if characters.get('SourceCharacter') is not None:
        src = characters['SourceCharacter']['Name']
    if characters.get('TargetCharacter') is not None:
        tgt = characters['TargetCharacter']['Name']
    return src, tgt


def element_renderer_action(element):
    content = element['content']
    if content in ignore_actions:
        return None

    src, tgt = characters_get(element)
    if content == 'ServerEnter':
        return "({} 进入房间)".format(src)
    elif content == 'ServerLeave':
        return "({} 离开房间)".format(src)
    elif content == 'ServerDisconnect':
        return "({} 离线)".format(src)
    elif content == 'CharacterNicknameUpdated':
        nick_old = dictionary_get(element['dictionary'], 'OldNick', 'Text')
        nick_new = dictionary_get(element['dictionary'], 'NewNick', 'Text')
        out = "({} is now known as {}.)".format(nick_old, nick_new)
        return out
    elif content in 'ActionUse':
        item = dictionary_get(element['dictionary'], 'NextAsset', 'AssetName')
        dest = dictionary_get(element['dictionary'], 'FocusAssetGroup', 'FocusGroupName')
        return "({} uses a {} on {}'s {}.)".format(src, item, tgt, dest)
    elif content in 'ActionSwap':
        prev_asset = dictionary_get(element['dictionary'], 'PrevAsset', 'AssetName')
        next_asset = dictionary_get(element['dictionary'], 'NextAsset', 'AssetName')
        desc = dictionary_get(element['dictionary'], 'FocusAssetGroup', 'FocusGroupName')
        return "({} swaps a {} for a {} on {}'s {}".format(src, prev_asset, next_asset, tgt, desc)
    elif content in 'ActionStruggle':
        prev_asset = dictionary_get(element['dictionary'], 'PrevAsset', 'AssetName')
        return "({} slips out of her {}.)".format(src, prev_asset)
    elif content in 'ActionUnlockAndRemove':
        prev_asset = dictionary_get(element['dictionary'], 'PrevAsset', 'AssetName')
        desc = dictionary_get(element['dictionary'], 'FocusAssetGroup', 'FocusGroupName')
        return "({} unlocks and removes the {} from {}'s {}.)".format(src, prev_asset, tgt, desc)
    elif ('VibeMode' in content or
          'TimerRelease' in content or
          'SlowLeaveAttempt' in content or
          'ItemArmsBitchSuitSet' in content or
          'ItemArmsHighStyleSteelCuffsSetWrist' in content):
        return None
    elif content == 'BCX_PLAYER_CUSTOM_DIALOG':
        return dictionary_get(element['dictionary'], 'MISSING PLAYER DIALOG: BCX_PLAYER_CUSTOM_DIALOG', 'Text')
    elif content == 'KneelDown':
        return "({} kneels down.)".format(src)
    elif content == 'StandUp':
        return "({} stands up.)".format(src)
    elif content == 'Beep':
        msg = dictionary_get(element['dictionary'], 'msg')
        if msg is None:
            msg = dictionary_get(element['dictionary'], 'Beep', 'Text')

        return "* Beep {} *".format(msg)
    elif content == 'HoldLeash':
        return "({} holds {}'s leash.)".format(src, tgt)

    elif content == 'ActionTightenLittle':
        prev_asset = dictionary_get(element['dictionary'], 'PrevAsset', 'AssetName')
        focus_group = dictionary_get(element['dictionary'], 'FocusAssetGroup', 'FocusGroupName')
        return "({} tightens the {} on {}'s {} a little.)".format(src, prev_asset, tgt, focus_group)
    else:
        # print("unknown action:\t", content, element)
        return None


def element_renderer_chat(element):
    name = element['sender']['name']
    # if len(name) > 6:
    #     name = name[:5] + ".."
    # else:
    #     name = name + "\t"

    content = element['content']
    return name, content


def element_renderer_activity(element):
    content = element['content']
    src, tgt = characters_get(element)
    asset = dictionary_get(element['dictionary'], 'ActivityAsset', 'AssetName')

    section = content.split('-')
    if ('LSCG_SharkBite' in content or
            'LSCG_ReleaseEar' in content):
        return None

    elif section[0] == 'ChatOther':
        do_action = section[2]
        do_target = convert_item(section[1])

        if do_action == 'Kiss':
            do_action = "亲吻"
        elif do_action == 'Hug':
            do_action = "拥抱"
        elif do_action == 'PoliteKiss':
            do_action = "轻吻"
        elif do_action == 'FrenchKiss':
            do_action = "深吻"
        elif do_action == 'Caress':
            do_action = "抚摸"
        elif do_action == "Bite":
            do_action = "咬"
        elif do_action == "Lick":
            do_action = "舔"
        elif do_action == "Nibble":
            do_action = "轻咬"
        elif do_action == "Whisper":
            do_action = "whispers in"
        elif do_action == "Pinch":
            do_action = "打"
        elif do_action == "Tickle":
            do_action = "挠"
        elif do_action == "Spank":
            do_action = "打"
        elif do_action == "Slap":
            do_action = "扇"
        elif do_action == "Gag":
            do_action = "塞"
        elif do_action == "Pull":
            do_action = "拉"
        elif do_action == "Tug":
            do_action = "拽"
        elif do_action == 'Pet':
            do_action = "拍"

        out = "({} {} {}的{}.)".format(src, do_action, tgt, do_target)

        if content == 'ChatOther-ItemEars-TickleItem':
            out = "({} tickles {}'s ear with {}.)".format(src, tgt, asset)

        elif content == 'ChatOther-ItemMouth-LSCG_GrabTongue':
            out = "({} grabs {}'s tongue.)".format(src, tgt)
        elif content == 'ChatOther-ItemMouth-GaggedKiss':
            out = "({} kisses {}'s gag.)".format(src, tgt)

        elif content == "ChatOther-ItemHead-TakeCare":
            out = "({} 给 {} 梳头.)".format(src, tgt)

        elif content == 'ChatOther-ItemArms-MassageHands':
            out = "({} massages {}'s hand.)".format(src, tgt)

        elif content == 'ChatOther-ItemHands-LSCG_HoldHand':
            out = "({} holds {}'s hand.)".format(src, tgt)
        elif content == 'ChatOther-ItemHands-LSCG_ReleaseHand':
            out = "({} release {}'s hand.)".format(src, tgt)

        elif content == 'ChatOther-ItemTorso-MassageHands':
            out = "({} massages {}'s back.)".format(src, tgt)

        elif content == 'ChatOther-ItemBreast-RestHead':
            out = "({} rests her head on {}'s breast.)".format(src, tgt)
        elif content == 'ChatOther-ItemBreast-MasturbateHand':
            out = "({} masturbates {}'s breast.)".format(src, tgt)


        elif content == 'ChatOther-ItemVulva-MasturbateHand':
            out = "({} masturbates {}'s vulva.)".format(src, tgt)
        elif content == 'ChatOther-ItemVulva-MasturbateFoot':
            out = "({} masturbates {}'s vulva with her foot.)".format(src, tgt)


        elif content == 'ChatOther-ItemNeck-MassageHands':
            out = "({} massages {}'s neck.)".format(src, tgt)


        elif content == 'ChatOther-ItemLegs-RestHead':
            out = "({} rests her head in {}'s lap.)".format(src, tgt)
        elif content == 'ChatOther-ItemLegs-TickleItem':
            out = "({} tickles {}'s thigh with {}.)".format(src, tgt, asset)
        elif content == 'ChatOther-ItemLegs-SpankItem':
            out = "({} spanks {}'s thigh with {}.)".format(src, tgt, asset)
        elif content == 'ChatOther-ItemLegs-Sit':
            out = "({} sits on {}'s lap.)".format(src, tgt)

        elif content == 'ChatOther-ItemButt-SpankItem':
            out = "({} spanks {}'s butt with {}.)".format(src, tgt, asset)

        elif content == 'ChatOther-ItemBoots-SpankItem':
            out = "({} spanks {}'s boots with {}.)".format(src, tgt, asset)
        # else:
        #     print("unknown activity:\t", content, element)
        #     out = "({} - {} - {})".format(src, tgt, content)

    elif 'ChatSelf-' in content:
        if content in ignore_activates:
            return None

        if '-RubItem' in content:
            tgt = content.split('-')[1]
            if tgt == 'ItemNose':
                tgt = 'nose'
            elif tgt == 'ItemMouth':
                tgt = 'mouth'
            elif tgt == 'ItemEars':
                tgt = 'ears'
            else:
                print("unknown self-rub target: {}".format(tgt))

            item = dictionary_get(element['dictionary'], 'ActivityAsset', 'AssetName')
            desc = dictionary_get(element['dictionary'], 'FocusAssetGroup', 'FocusGroupName')
            out = "(She rubs her {} with {} from her {}.)".format(tgt, item, desc)
        elif content == 'ChatSelf-ItemEars-Wiggle':
            out = "({} wiggles her ears.)".format(src)
        elif content == 'ChatSelf-ItemEars-Caress':
            out = "({} caresses her ears.)".format(src)

        elif content == 'ChatSelf-ItemMouth-Lick':
            out = "({} licks her lips.)".format(src)
        elif content == 'ChatSelf-ItemMouth-HandGag':
            out = "({} clamps her hand over her mouth.)".format(src)
        elif content == 'ChatSelf-ItemMouth-MoanGagWhimper':
            out = "({} moans into her gag.)".format(src)

        elif content == 'ChatSelf-ItemHead-Wiggle':
            out = "({} wiggles her head.)".format(src)
        elif content == 'ChatSelf-ItemHead-Caress':
            out = "({} caresses her face.)".format(src)
        elif content == 'ChatSelf-ItemHead-TakeCare':
            out = "({} brushes her hair.)".format(src)
        elif content == 'ChatSelf-ItemHead-Nod':
            out = "({} nods.)".format(src)
        elif content == 'ChatSelf-ItemHead-Pet':
            out = "({} pets her head.)".format(src)

        elif content == 'ChatSelf-ItemNipples-Caress':
            out = "({} caresses her nipples.)".format(src)

        elif content == 'ChatSelf-ItemBreast-Wiggle':
            out = "({} wiggles her breasts.)".format(src)

        elif content == 'ChatSelf-ItemArms-StruggleArms':
            out = "({} struggles against her bonds.)".format(src)
        elif content == 'ChatSelf-ItemArms-Lick':
            out = "({} licks her arms.)".format(src)
        elif content == 'ChatSelf-ItemArms-Wiggle':
            out = "({} wiggles her arms.)".format(src)


        elif content == 'ChatSelf-ItemVulvaPiercings-MasturbateHand':
            out = "({} masturbates her vulva.)".format(src)
        elif content == 'ChatSelf-ItemVulvaPiercings-Slap':
            out = "({} slaps her vulva.)".format(src)
        elif content == 'ChatSelf-ItemVulvaPiercings-Caress':
            out = "({} caresses her vulva.)".format(src)

        elif content == 'ChatSelf-ItemButt-Wiggle':
            out = "({} wiggles her butt.)".format(src)

        elif content == 'ChatSelf-ItemLegs-Wiggle':
            out = "({} wiggles her legs.)".format(src)

        else:
            print("unknown activity:\t", content, element)
            out = None

    elif 'Orgasm' in content:
        out = None
    else:
        print("unknown activity:", element)
        out = "({} - {})".format(src, content)

    return out


def element_renderer_emote(element):
    name = element['sender']['name']
    content = element['content']
    if content is None or content == '':
        return None
    elif content[0] == '*':
        return "*\t{}".format(content[1:].replace('\n', '\n\t\t *\t'))
    else:
        return "({} {})".format(name, content)


def element_renderer_whisper(element):
    if element.get('target') is not None:
        target = json.loads(element.get('target'))['name']
    else:
        target = json.loads(element.get('session'))['name']
    print(element)
    sender = json.loads(element.get('sender'))['name']
    content = element['content']
    name = '悄悄话 {} to {}'.format(sender, target)
    return name, content


def element_renderer_servermessage(element):
    name = element['sender']['name']
    content = element['content']
    return "({}: {})".format(name, content)
