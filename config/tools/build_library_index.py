"""Rebuild the offline index and model entry pages from the unified catalog."""
from pathlib import Path
from collections import defaultdict
import html,json

ROOT=Path(__file__).resolve().parents[2]

def main():
    entries=json.loads((ROOT/'config/catalog.json').read_text(encoding='utf8'))['textures']
    groups=defaultdict(list)
    rows=[]
    for a in entries:
        groups[(a['category'],a['id'])].append(a)
        links=' · '.join(f'<a href="{html.escape(a["path"]+"/"+file,quote=True)}">{label}</a>' for file,label in [('island_ids.png','分区编号'),('outline.svg','矢量轮廓'),('outline.png','轮廓图'),('coverage_mask.png','覆盖蒙版'),('islands.csv','分区坐标'),('boundary_coordinates.csv','边界坐标'),('geometry.npz','UV/XYZ'),('metadata.json','来源')])
        if a.get('seam_database'):
            links+=f' · <a href="{a["seam_database"]}">单像素接缝库</a>'
        rows.append(f'<tr data-category="{a["category"]}"><td>{"飞机" if a["category"]=="aircraft" else "导弹"}</td><td>{html.escape(a["id"])}</td><td>{html.escape(a["model"])}</td><td>{html.escape(a["texture"])}</td><td>{a["width"]}×{a["height"]}</td><td>{links}</td></tr>')
    for (category,alias),items in groups.items():
        lines=[f'# {alias}', '', f'原生型号：`{items[0]["model"]}`。', '', '`_c` 布局已收录；`_n` 暂按共用布局处理，实际制作时用模拟渲染确认。', '', '| 贴图 | 制作尺寸 | 轮廓与坐标 |', '|---|---|---|']
        for a in items:
            t=a['texture'];lines.append(f'| `{t}` | {a["width"]}×{a["height"]} | [编号图]({t}/island_ids.png) · [轮廓]({t}/outline.svg) · [边界坐标]({t}/boundary_coordinates.csv) · [来源]({t}/metadata.json) |')
        if category=='missiles':
            lines+=['','接缝树保留该贴图的全部原生 LOD0 几何，未进行静态外表面筛选。每张贴图独立建树，不虚构跨贴图连接。短线宽 1 像素、每侧 1–7 个采样点，仅存于数据库。','', '```powershell']
            a=items[0]
            lines += [f'python config/tools/query_seams.py --db {a["seam_database"]} --model {a["model"]}', '```', '', '以上命令从仓库根目录运行。模型分区、空间间隙和亚像素回算不等于游戏内外观验证。']
        else:
            lines+=['','[飞机复核范围与限制](../../config/reviews/2026-11-06/验收范围.md)。J15T 保留原版主贴图基准。']
        (ROOT/category/alias/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>涂装轮廓库</title><style>body{font:16px system-ui;margin:24px;color:#222;line-height:1.7}input,select{font:inherit;padding:8px}table{border-collapse:collapse;width:100%;margin-top:20px}td,th{padding:9px;text-align:left;border-bottom:1px solid #ddd}a{color:#245a91}code{background:#eee}</style><h1>涂装轮廓库</h1><p>飞机 6 型 / 107 张布局；导弹 27 型 / 29 张布局。全部为 _c；_n 假定共用，待使用时模拟渲染确认。</p><p><a href="README.md">使用说明</a> · <a href="config/catalog.csv">目录表</a> · <a href="config/validation/library_validation.json">整理校验</a> · <a href="config/docs/missiles.md">导弹范围与限制</a></p><p>坐标：x=u×W，y=(1-v)×H。短连线只存数据库，不画入轮廓或涂装。尺寸以每张 metadata.json 为准。</p><select id="kind"><option value="">全部</option><option value="aircraft">飞机</option><option value="missiles">导弹</option></select> <input id="query" placeholder="搜索型号或贴图名"><table><thead><tr><th>分类</th><th>型号</th><th>原生名称</th><th>贴图</th><th>制作尺寸</th><th>文件</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table><script>function filter(){let q=document.querySelector('#query').value.toLowerCase(),k=document.querySelector('#kind').value;for(let r of document.querySelectorAll('tbody tr'))r.hidden=!!((k&&r.dataset.category!==k)||!r.innerText.toLowerCase().includes(q))}document.querySelector('#query').oninput=filter;document.querySelector('#kind').onchange=filter;</script></html>'''
    (ROOT/'index.html').write_text(page,encoding='utf8')
    print(f'INDEX_OK {len(entries)} layouts / {len(groups)} models')

if __name__=='__main__':main()
