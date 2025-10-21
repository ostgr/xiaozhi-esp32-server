# get_news_from_newsnow Plugin News Source Configuration Guide

## Overview

The `get_news_from_newsnow` plugin now supports dynamically configuring news sources through the Web management interface, no longer requiring code modifications. Users can configure different news sources for each agent in the control panel.

## Configuration Methods

### 1. Web Management Interface Configuration (Recommended)

1. Login to the control panel
2. Go to "Role Configuration" page
3. Select the agent you want to configure
4. Click "Edit Functions" button
5. Find the "newsnow news aggregation" plugin in the right parameter configuration area
6. Enter semicolon-separated Chinese names in the "News Source Configuration" field

### 2. Configuration File Method

Configure in `config.yaml`:

```yaml
plugins:
  get_news_from_newsnow:
    url: "https://newsnow.busiyi.world/api/s?id="
    news_sources: "The Paper;Baidu Hot Search;Cailian Press;Weibo;Douyin"
```

## News Source Configuration Format

News source configuration uses semicolon-separated Chinese names, format:

```
Chinese Name 1;Chinese Name 2;Chinese Name 3
```

### Configuration Example

```
The Paper;Baidu Hot Search;Cailian Press;Weibo;Douyin;Zhihu;36Kr
```

## Supported News Sources

The plugin supports the following Chinese names for news sources:

- The Paper (澎湃新闻)
- Baidu Hot Search (百度热搜)
- Cailian Press (财联社)
- Weibo (微博)
- Douyin (抖音)
- Zhihu (知乎)
- 36Kr (36氪)
- Wall Street Journal (华尔街见闻)
- IT Home (IT之家)
- Toutiao (今日头条)
- Hupu (虎扑)
- Bilibili (哔哩哔哩)
- Kuaishou (快手)
- Xueqiu (雪球)
- Gelonghui (格隆汇)
- Fabu Finance (法布财经)
- Jin10 Data (金十数据)
- Nowcoder (牛客)
- Sspai (少数派)
- Juejin (稀土掘金)
- Phoenix News (凤凰网)
- Chongbuluo (虫部落)
- Zaobao (联合早报)
- Coolapk (酷安)
- CleanTechnica Forum (远景论坛)
- Reference News (参考消息)
- Sputnik News (卫星通讯社)
- Baidu Tieba (百度贴吧)
- Reliable News (靠谱新闻)
- And more...

## Default Configuration

If no news sources are configured, the plugin will use the following default configuration:

```
The Paper;Baidu Hot Search;Cailian Press
```

## Usage Instructions

1. **Configure News Sources**: Set Chinese names of news sources in the Web interface or configuration file, separated by semicolons
2. **Call Plugin**: Users can say "broadcast news" or "get news"
3. **Specify News Source**: Users can say "broadcast The Paper news" or "get Baidu Hot Search"
4. **Get Details**: Users can say "give me detailed information about this news"

## Working Principle

1. Plugin accepts Chinese names as parameters (e.g., "The Paper")
2. Based on the configured news source list, converts Chinese names to corresponding English IDs (e.g., "thepaper")
3. Uses English ID to call API to get news data
4. Returns news content to user

## Notes

1. Configured Chinese names must exactly match the names defined in CHANNEL_MAP
2. Service restart or configuration reload required after configuration changes
3. If configured news sources are invalid, plugin will automatically use default news sources
4. Use English semicolon (;) to separate multiple news sources, not Chinese semicolon (；)
