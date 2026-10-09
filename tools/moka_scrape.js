#!/usr/bin/env node
/*
 * MokaHR (mokahr.com) 公开招聘站点采集器
 * 用法: node tools/moka_scrape.js <站点页面URL> <输出文件>
 *   node tools/moka_scrape.js 'https://apply.careers.dji.com/social-recruitment/dji/168240?locale=zh-CN' out.json
 * 原理: 页面 TurboApply.data.aesIv 作为 IV; POST /api/outer/ats-apply/website/jobs/v2
 *       返回 {data:<base64>, necromancer:<key>} -> AES-128-CBC 解密
 * 环境变量 MOKA_IV 可强制指定 IV (若页面 302/无 aesIv)。
 */
const fs = require('fs');
const crypto = require('crypto');
const https = require('https');
const { URL } = require('url');

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';

function httpGet(url, depth) {
  depth = depth || 0;
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    https.get({ hostname: u.hostname, path: u.pathname + u.search, headers: { 'User-Agent': UA, 'Accept': 'text/html,*/*' }, timeout: 40000 }, res => {
      if ([301, 302, 303, 307, 308].indexOf(res.statusCode) >= 0 && res.headers.location && depth < 5) {
        res.resume();
        return resolve(httpGet(new URL(res.headers.location, url).toString(), depth + 1));
      }
      let d = ''; res.setEncoding('utf8');
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d, headers: res.headers }));
    }).on('error', reject).on('timeout', () => reject(new Error('timeout')));
  });
}

function httpPost(url, body, referer) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const payload = Buffer.from(JSON.stringify(body), 'utf8');
    const req = https.request({
      hostname: u.hostname, path: u.pathname + u.search, method: 'POST',
      headers: {
        'User-Agent': UA, 'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Origin': u.origin, 'Referer': referer || (u.origin + '/'),
        'Content-Length': payload.length
      }, timeout: 40000
    }, res => {
      let d = ''; res.setEncoding('utf8');
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d }));
    });
    req.on('error', reject); req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(payload); req.end();
  });
}

function decrypt(dataB64, keyStr, ivStr) {
  const key = Buffer.from(keyStr, 'utf8');
  const iv = ivStr ? Buffer.from(ivStr, 'utf8') : Buffer.alloc(16, 0);
  const alg = key.length === 32 ? 'aes-256-cbc' : (key.length === 24 ? 'aes-192-cbc' : 'aes-128-cbc');
  const d = crypto.createDecipheriv(alg, key, iv);
  return Buffer.concat([d.update(Buffer.from(dataB64, 'base64')), d.final()]).toString('utf8');
}

let AES_IV = '';
function parseResp(txt) {
  let j;
  try { j = JSON.parse(txt); } catch (e) { return null; }
  if (j && j.necromancer && j.data) {
    let plain;
    try { plain = decrypt(j.data, j.necromancer, AES_IV); } catch (e) { return { __decrypt_error: e.message }; }
    try { return JSON.parse(plain); } catch (e) { return { __raw: plain }; }
  }
  return j;
}

async function main() {
  const siteUrl = process.argv[2];
  const outFile = process.argv[3];
  if (!siteUrl || !outFile) { console.error('usage: node moka_scrape.js <siteUrl> <outFile>'); process.exit(1); }
  const m = siteUrl.match(/([a-z-]*recruitment)\/([A-Za-z0-9_.-]+)\/(\d+)/);
  if (!m) { console.error('cannot parse org/site from url'); process.exit(1); }
  const orgId = m[2], siteId = Number(m[3]);
  const u = new URL(siteUrl);
  const apiBase = u.origin;

  const page = await httpGet(siteUrl);
  let iv = process.env.MOKA_IV || '';
  let mm = page.body.match(/&quot;aesIv&quot;:&quot;([^&]+)&quot;/) || page.body.match(/"aesIv":"([^"]+)"/);
  if (mm) iv = mm[1];
  AES_IV = iv;
  console.error('[moka] org=' + orgId + ' site=' + siteId + ' iv=' + iv + ' pageHttp=' + page.status);

  const all = [];
  const size = 50;
  let pageNo = 1;
  for (;;) {
    const r = await httpPost(apiBase + '/api/outer/ats-apply/website/jobs/v2',
      { orgId: orgId, siteId: siteId, limit: size, offset: (pageNo - 1) * size, needStat: true, locale: 'zh-CN' }, siteUrl);
    const j = parseResp(r.body);
    if (!j || !j.data || !j.data.jobs) { console.error('[moka] page ' + pageNo + ' no jobs http=' + r.status + ' ' + String(r.body).slice(0, 160)); break; }
    const jobs = j.data.jobs;
    all.push.apply(all, jobs);
    const total = (j.data.jobStats && j.data.jobStats.total) || jobs.length;
    console.error('[moka] page ' + pageNo + ' got ' + jobs.length + ' total ' + total);
    if (all.length >= total || jobs.length === 0) break;
    pageNo++;
    if (pageNo > 60) break;
  }
  const out = { orgId: orgId, siteId: siteId, siteUrl: siteUrl, aesIv: iv, collected_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z'), total: all.length, jobs: all };
  fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
  console.error('[moka] saved ' + all.length + ' jobs -> ' + outFile);
}
main().catch(e => { console.error('ERR', e.message); process.exit(1); });
