"""Generate UTF-8 SRT from reviewed 10-fps cue timings, without copying movies."""
import hashlib,json
from fontTools.ttLib import TTFont
from build_paths import ROOT,FONT


def stamp(frame):
    millis=frame*100
    return f'{millis//3600000:02}:{millis//60000%60:02}:{millis//1000%60:02},{millis%1000:03}'


def main():
    rows=json.loads((ROOT/'translation/movie_subtitles.json').read_text(encoding='utf-8'))
    durations=json.loads((ROOT/'translation/movie_durations.json').read_text(encoding='utf-8'))
    out=ROOT/'build/movie-subtitles';out.mkdir(parents=True,exist_ok=True)
    font=TTFont(FONT,fontNumber=0)
    cmap=font.getBestCmap();assets=[]
    for movie,name in [('PJ','PJ'),('ED4','Ed4'),('ED5','Ed5')]:
        cues=[r for r in rows if r['movie']==movie];last=0;blocks=[]
        for i,row in enumerate(cues,1):
            if not last<=row['start']<row['end']<=durations[movie]*10:
                raise ValueError(f'Invalid or overlapping movie cue: {movie}/{i}')
            if not row['ko'] or any(ord(c) not in cmap for c in row['ko'] if not c.isspace()):
                raise ValueError(f'Movie cue has missing Korean glyphs: {movie}/{i}')
            blocks.append(f"{i}\n{stamp(row['start'])} --> {stamp(row['end'])}\n{row['ko']}\n")
            last=row['end']
        path=out/f'{name}.srt'
        path.write_bytes(('\n'.join(blocks)+'\n').replace('\n','\r\n').encode('utf-8'))
        assets.append({'file':path.name,'cues':len(cues),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    if len(rows)!=28 or sum(a['cues'] for a in assets)!=28:
        raise ValueError('Expected all 28 reviewed movie cues')
    print(json.dumps(assets))


if __name__=='__main__':main()
