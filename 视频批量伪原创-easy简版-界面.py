import os
import threading
from moviepy.config import change_settings
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from datetime import datetime
import ast
import random
from openai import OpenAI
import PySimpleGUI as sg

# 配置 ImageMagick 的路径
change_settings({"IMAGEMAGICK_BINARY": r"D:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})
jsonFile=""
aweme_pro_list=[]
# 配色方案
def random_color_scheme():
    schemes = [
        {"color": "white", "bg_color": "black", "stroke_color": "black"},
        {"color": "white", "bg_color": "#F1FAFA", "stroke_color": "#888888"},
        {"color": "black", "bg_color": "#E8E8FF", "stroke_color": "transparent"},
        {"color": "white", "bg_color": "#336699", "stroke_color": "transparent"},
        {"color": "#007BFF", "bg_color": "#FFA500", "stroke_color": "transparent"},
        {"color": "#8B0000", "bg_color": "#FFB6C1", "stroke_color": "transparent"}
    ]
    return random.choice(schemes)

def add_text_overlay_and_resize(video_path, text, output_path, log_element):
    try:
        clip = VideoFileClip(video_path)
        text_width = int(clip.size[0] * 0.8)
        color_scheme = random_color_scheme()
        txt_clip = TextClip(
            text,
            fontsize=24,
            color=color_scheme["color"],
            bg_color=color_scheme["bg_color"],
            size=(text_width, None),
            method="label",
            align="Center",
            font="SimHei",
            stroke_color=color_scheme["stroke_color"],
            stroke_width=2
        )
        txt_clip = txt_clip.set_position((("center", 60))).set_duration(clip.duration)
        resized_clip = clip.resize(1.1)
        cropped_clip = resized_clip.crop(
            x_center=clip.size[0] / 2,
            y_center=clip.size[1] / 2,
            width=clip.size[0],
            height=clip.size[1]
        )
        composite_clip = CompositeVideoClip([cropped_clip, txt_clip])
        composite_clip.write_videofile(output_path, codec="libx264", fps=clip.fps)
        log_element.update(f"视频处理完成，已保存到 {output_path}\n", append=True)
    except Exception as e:
        log_element.update(f"处理视频时发生错误：{e}\n", append=True)

def generate_AI_title_aliQWEN(prompt_title, log_element):
    myRule = "以营销广告为目的，提炼带货短视频中使用的话题短标题或关键词或卖点短句，对以下标题进行提炼，大胆创新，可以夸张，每次提炼角度不同，忽略原标题中的价格及促销信息，要求改写后短标题长度字数在4-10个汉字内，返回短标题本身即可，不要返回多余的提示分析序号等，只返回短标题自身内容即可。原标题如下:\n\n"
    api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    api_key = "sk-8b05a833b5d44c6883a8d09b417d0e12"
    client = OpenAI(api_key=api_key, base_url=api_base)
    completion = client.chat.completions.create(
        model="qwen-plus-latest",
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': myRule + prompt_title}
        ],
    )
    newTitle = completion.choices[0].message.content
    newTitle = newTitle.replace('"', '')
    log_element.update(f"生成标题：{newTitle}\n", append=True)
    return newTitle

#　need取得导入数据源json文件
def importJson(jsonFile):
    apList=[] #aweme_pro_list
    with open(jsonFile, 'r', encoding='utf-8') as f:  # 打开文件
        lines = f.readlines()  # 读取所有行
        jsonListStr = lines[0]  # 取第一行 # apList = json.loads(jsonListStr) 
        if len(lines)>1:            
            jsonListStr = ''.join(lines)# 将所有行拼接成一个完整的字符串
         
                   
        apList = ast.literal_eval(jsonListStr)        
    return apList

def process_videos(sourcePath, outputPath, log_element):
    mp4_files = [f for f in os.listdir(sourcePath) if f.endswith('.mp4')]
    total = len(mp4_files)
    i = 1

    for mp4_file in mp4_files:
        log_element.update(f"===处理进度: {i}/{total} ===\n", append=True)
        file_prefix = os.path.splitext(mp4_file)[0]
        if " " in file_prefix:
            prompt_title = file_prefix.split(" ", 1)[1]
        else:
            prompt_title = file_prefix

        if len(prompt_title)==5:
            oid=prompt_title.strip("-")
            VT=""
            #从JSON中取数据 得到标题 jsonFile中视频标题 VT
            for apItem in aweme_pro_list:
                if apItem['oid']==oid:
                    VT=apItem['atitle']                    
                    if VT=="":
                        VT=apItem['protitle']
                    break
            prompt_title=VT
        print(f"当前标题 / oid:{prompt_title}")
        short_title = generate_AI_title_aliQWEN(prompt_title, log_element)

        sourceVideo = os.path.join(sourcePath, mp4_file)
        outputVideo = os.path.join(outputPath, mp4_file)
        add_text_overlay_and_resize(sourceVideo, short_title, outputVideo, log_element)
        i += 1

    log_element.update("处理完成！\n", append=True)

# GUI 布局
layout = [
    [sg.Text("素材文件夹："), sg.Input(key="-SOURCE-", readonly=True), sg.FolderBrowse()],
    [sg.Text("输出文件夹："), sg.Input(key="-OUTPUT-", readonly=True), sg.FolderBrowse()],

    [sg.Text("**JSON文件: "), sg.Input(key="-JSONFILE-", ), sg.FileBrowse()],
    
    [sg.Text('线程:',font=("微软雅黑", 10)),sg.Input(default_text=3, key='threadNum',size=(3, 1),tooltip="英文输入法1-10数字"),  
     sg.Button("开始处理",button_color ='Orange'), sg.Button("退出",button_color ='Red')],
    [sg.Multiline(size=(66, 10), key="-LOG-", autoscroll=True, disabled=True)]
]

# 创建窗口
window = sg.Window("视频处理工具", layout)

# 事件循环
while True:
    event, values = window.read()
    if event == "退出" or event == sg.WINDOW_CLOSED:
        break
    elif event == "开始处理":
        sourcePath = values["-SOURCE-"]
        outputPath = values["-OUTPUT-"]
        jsonFile = values["-JSONFILE-"]
        if len(jsonFile)>24:
            aweme_pro_list=importJson(jsonFile) #apList


        if not sourcePath or not outputPath:
            sg.popup("请先选择素材源文件夹和输出文件夹！")
            continue

        # 使用多线程处理视频
        threading.Thread(target=process_videos, args=(sourcePath, outputPath, window["-LOG-"]), daemon=True).start()

# 关闭窗口
window.close()



# pyinstaller -F -w -i jdMatch.ico 视频批量伪原创-easy简版-界面.py 
