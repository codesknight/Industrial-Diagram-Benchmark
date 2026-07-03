# Watermark Scan Report

This report scans filenames/paths and Raw JSON text entities for watermark/source keywords.

## Summary

- Total rows scanned: 2054
- Watermark candidate rows: 597
- High confidence rows: 12
- Medium confidence rows: 585

## Recommendation

- High confidence: filter from clean training/evaluation or place in a separate watermark split.
- Medium confidence: review before filtering; filename/source marker may not be visibly rendered.
- Do not delete raw files. Keep filtering manifest-based.

## Keyword Counts

- taobao: 591
- wm666: 585
- 淘宝: 6
- 图库: 7
- 星欣: 7

## First Candidates

| drawing_key | confidence | metadata_hits | json_text_hits |
|---|---|---|---|
| `_P1_staging/#2主变220kV侧DL机构二次接线图(B066-500-0301)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变220kV侧DL端子箱二次安装图(B066-500-0308)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变35kV侧DL机构二次接线图(B066-500-0304)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变35kV侧DL端子箱二次安装图(B066-500-0309)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变500kV侧PT二次接线和安装图(B066-500-0307)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变录波柜二次接线图(B066-500-0215)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变录波柜端子排图(B066-500-0219)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变本体总控制箱端子排图(B066-500-0310)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变测控单元控制信号回路(B066-500-0202)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变测控柜A16端子排图(B066-500-0218)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变测量计度回路(B066-500-0201)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变风冷控制回路(一)(B066-500-0213)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变风冷控制回路(二)(B066-500-0214)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/#2主变风冷控制箱二次安装图(B066-500-0311)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/01-110KV屋外配电装置配置接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/02-110KV屋外配电装置平面布置图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/02-主接线wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/03-10kV配电装置主变进线及母线桥间隔断面图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/03-110KV屋外配电装置出线间隔断面图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/04-110KV屋外配电装置主变进线间隔及母线PT间隔断面图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/05-110KV屋外配电装置母线分段间隔断面图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV出线断面图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV升压站平面布置图1wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV升压站总体平面布置图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV升压站接地布置图.wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV升压站立面布置图1wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV升压站立面布置图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV变电站主接线保护直流所wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110KV变电站典型设计图纸wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110Kv变电站直流系统接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kVxx变电站完整电源图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kVxx变电站完整电源图（塔位点）wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kV变电站GIS布置平面图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kV变电站电气主接线wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kV变电站远动范围图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kV开关站+ABB避雷针高度计算` | high |  | taobao;淘宝 |
| `_P1_staging/110kV部分wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kV降压变电站主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kv变电站电气一次图纸目录wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kv变电站电气一次说明书wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/110kv安斑东线、西线竣工图设计wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/132kV变电站主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/16-主变及35kV场地平面布置图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/2-主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/220Kv枢纽变电站主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/250kVA欧式箱变电气主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35KV变电站主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变35kv侧开关控制信号回路原理接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变35kv侧开关柜端子排图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变6kv侧开关控制信号回路原理接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变6kv侧开关柜端子排图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变保护屏端子排图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变保护高低压侧电流电压回路原理接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变压器调压、分接头遥信接口回路图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/35kv江鑫－主变瓦斯、温度、油位、接口回路图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/500KV电站主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/D-02 电气主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/D-04 500kV GIS主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/XX变电站主接线图1wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/XX变电站主接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/xx110kV出线平面布置图Awm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/三卷主变电流电压回路wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/三卷主变面板图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变.35kV侧隔离开关操作机构二次接线图(B066-500-0305)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变35kV侧接地刀操作机构二次接线图(B066-500-0306)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变低压侧电缆安装示意图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护A柜接线图(一)(B066-500-0203)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护A柜接线图(三)(B066-500-0205)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护A柜接线图(二)(B066-500-0204)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护A柜接线图(四)(B066-500-0206)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护A柜端子箱(B066-500-0216)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护B柜接线图(一)(B066-500-0207)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护B柜接线图(三)(B066-500-0209)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护B柜接线图(二)(B066-500-0208)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护B柜接线图(四)(B066-500-0210)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护B柜端子排图(B066-500-0217)wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护与信号回路接线图2wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护与信号回路接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护及信号回路接线图wm666.taobao.com` | medium | taobao;wm666 |  |
| `_P1_staging/主变保护测控屏背面接线图wm666.taobao.com` | medium | taobao;wm666 |  |
