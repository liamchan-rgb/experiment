#!/usr/bin/env python3
"""Check the pilot's user-facing contracts: fixed gait, layers and exports."""
import base64
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image, ImageSequence
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Art/Templates/P1-Down/v1'


def rgba(im):
    a = np.array(im.convert('RGBA'))
    a[a[:, :, 3] == 0] = 0
    return a


def premultiplied(im):
    a = rgba(im).astype(float)
    a[:, :, :3] *= a[:, :, 3:4] / 255
    return a


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    m = json.loads((OUT / 'manifest.json').read_text())
    lock = json.loads((ROOT / 'Art/Templates/P1-Motion-v1.json').read_text())
    assert len(lock['directions']) == 8
    for direction in lock['directions'].values():
        assert digest(ROOT / direction['approval']) == direction['approvalSHA256']
        for f in direction['frames']:
            assert digest(ROOT / f['path']) == f['sha256']
    refs = [Image.open(OUT / 'reference' / f'{i:02}.png') for i in range(9)]
    assert len({digest(OUT / 'reference' / f'{i:02}.png') for i in range(1, 9)}) == 8
    default = Image.open(OUT / 'appearances/chestnut-blue-traveler-empty.png')
    for i, ref in enumerate(refs):
        assert np.array_equal(rgba(default.crop((i*256, 0, (i+1)*256, 256))), rgba(ref)), i
    checked = 0
    for appearance in m['combinations']:
        atlas = Image.open(OUT / appearance['atlas'])
        assert atlas.size == (2304, 256)
        for i in range(9):
            frame = atlas.crop((i*256, 0, (i+1)*256, 256))
            f = m['frames'][i]
            ref = rgba(refs[i])
            yy, xx = np.indices((256, 256))
            # Actual leg/boot pixels, excluding coat tails and the outside sword.
            leg = (yy >= 185) & (xx >= 104) & (xx < 147) & (ref[:, :, 3] > 96)
            assert np.array_equal(rgba(frame)[leg], ref[leg]), (appearance['key'], i)
            # Nothing touches the 256px cell edge, including the sword.
            a = rgba(frame)[:, :, 3]
            assert not np.any(np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]]))
            hand = Image.open(OUT / 'layers' / f'{i:02}' / 'hands.png')
            weapon = Image.open(OUT / 'layers' / f'{i:02}' / 'weapon-sword.png')
            x, y = f['rightHand']
            assert hand.getpixel((x, y))[3] > 128, ('hand anchor outside hand', i)
            assert weapon.getpixel((x, y))[3] > 128, ('grip outside sword', i)
            checked += 1
    ora_count = 0
    for p in sorted((OUT / 'editable').rglob('*.ora')):
        with zipfile.ZipFile(p) as z:
            assert z.infolist()[0].filename == 'mimetype'
            assert z.infolist()[0].compress_type == zipfile.ZIP_STORED
            assert z.read('mimetype') == b'image/openraster'
            stack = ET.fromstring(z.read('stack.xml')).find('stack')
            rebuilt = Image.new('RGBA', (256, 256))
            for el in reversed(list(stack)):
                if el.get('visibility') != 'hidden':
                    rebuilt.alpha_composite(Image.open(io.BytesIO(z.read(el.get('src')))))
            expected = Image.open(io.BytesIO(z.read('mergedimage.png')))
            assert np.array_equal(rgba(rebuilt), rgba(expected)), p
            atlas = Image.open(OUT / 'appearances' / (p.parent.name+'.png'))
            i = int(p.stem)
            assert np.array_equal(rgba(expected), rgba(atlas.crop((i*256, 0, (i+1)*256, 256)))), p
        ora_count += 1
    for p in (OUT / 'review').glob('*.gif'):
        g = Image.open(p)
        ms = 480 if 'slow' in p.name else 120
        assert g.n_frames == 8 and g.info['loop'] == 0
        assert all(f.info['duration'] == ms for f in ImageSequence.Iterator(g))

    errors, requests = [], []
    browser_deltas = []
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True,
                                     args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, accept_downloads=True)
        page.clock.install()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda req: requests.append(req.url))
        page.route('**/*', lambda route: route.abort())
        # Managed Chromium blocks file:// navigation. set_content exercises the
        # exact self-contained HTML with all network requests blocked instead.
        page.set_content((OUT / 'preview.html').read_text())
        page.evaluate('window.__templateReady')
        page.evaluate('templatePilot.state.playing=false;templatePilot.render()')
        rendered = page.evaluate('''() => {
          const results=[];
          for(const item of templatePilot.manifest.combinations){
            for(const [k,v] of Object.entries(item.selection))templatePilot.select(k,v);
            const c=document.createElement('canvas');c.width=2304;c.height=256;
            const ctx=c.getContext('2d');
            for(let i=0;i<9;i++)ctx.drawImage(templatePilot.composite(i),i*256,0);
            results.push({key:item.key,png:c.toDataURL('image/png').split(',')[1]});
          }return results;
        }''')
        for item in rendered:
            actual = Image.open(io.BytesIO(base64.b64decode(item['png'])))
            expected = Image.open(OUT / 'appearances' / (item['key']+'.png'))
            delta = float(np.max(np.abs(premultiplied(actual)-premultiplied(expected))))
            assert delta <= 2.5, (item['key'], delta)
            browser_deltas.append(delta)
        # Exercise real controls and downloads, not only the compositor API.
        for slot, value in {'hair':'silver','face':'amber','outfit':'ranger','weapon':'sword'}.items():
            page.locator(f'[data-slot="{slot}"] [data-value="{value}"]').click()
        page.locator('[data-frame="4"]').click()
        assert page.evaluate('templatePilot.state.frame') == 4
        assert not page.evaluate('templatePilot.state.playing')
        page.locator('#play').click()
        page.clock.run_for(140)
        assert page.evaluate('templatePilot.state.frame') == 5
        page.locator('#speed').select_option('480')
        page.clock.run_for(400)
        assert page.evaluate('templatePilot.state.frame') == 5
        page.clock.run_for(110)
        assert page.evaluate('templatePilot.state.frame') == 6
        page.locator('[data-frame="4"]').click()
        page.locator('#anchors').check()
        # Layer isolation reveals the supplied head/torso fill, then restores it.
        page.locator('summary').click()
        page.locator('[data-layer="hair"]').uncheck()
        page.locator('[data-layer="hair"]').check()
        page.locator('summary').click()
        for button, name in [('export-frame','frame.png'),('export-atlas','atlas.png'),('export-config','look.json')]:
            with page.expect_download() as download:
                page.locator('#'+button).click()
            download.value.save_as(str(Path(tmp)/name))
        assert Image.open(Path(tmp)/'frame.png').size == (256,256)
        assert Image.open(Path(tmp)/'atlas.png').size == (2304,256)
        cfg = json.loads((Path(tmp)/'look.json').read_text())
        assert cfg['selection'] == {'hair':'silver','face':'amber','outfit':'ranger','weapon':'sword'}
        assert cfg['frameMs'] == 480
        expected = Image.open(OUT / 'appearances/silver-amber-ranger-sword.png')
        assert np.max(np.abs(premultiplied(Image.open(Path(tmp)/'atlas.png'))-premultiplied(expected))) <= 2.5
        page.locator('#anchors').uncheck()
        page.locator('[data-frame="1"]').click()
        page.screenshot(path=str(OUT/'review/preview-desktop.png'), full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(OUT/'review/preview-mobile.png'),full_page=True)
        assert not errors, errors
        assert not [r for r in requests if not r.startswith('data:')], requests
        browser.close()
    report = {'date':'2026-10-18','artApproval':None,'approvedMotionFramesLocked':72,
              'defaultVisibleRGBAEqualsApprovedFrames':9,'appearancePoseCombinations':checked,
              'legAndBootPixelsUnchangedAcrossAllCombinations':True,
              'handAndGripAnchorsInsideArtwork':True,'noCellEdgeClipping':True,
              'openRasterVisibleLayerReassemblyMatches':ora_count,
              'gifWalkFrames':8,'gifFrameMs':[120,480],
              'browserAtlasesMatchOfflineExports':len(browser_deltas),
              'maxBrowserPremultipliedChannelDelta':max(browser_deltas),
              'browserControlsAndThreeDownloadsPassed':True,
              'desktopAnd390pxMobileLayoutPassed':True,'externalNetworkRequests':0,
              'browserFileNavigation':'managed Chromium blocks file://; tested identical HTML via set_content with requests blocked',
              'nativeEditorGUIOrApplicationBuild':'not run; ORA structurally/recomposition checked, no native app changes',
              'note':'Checks verify export and customization invariants, not user artwork approval.'}
    (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
