# OpenRouter API アップデート調査メモ (2026年1月10日)

2026年1月10日のOpenRouter公式アナウンスおよび、その後のAPIドキュメント調査の結果をまとめたメモです。

## 1. 主要なアップデート内容

- **Auto Router の強化**: Opus 4.5 や GPT-5 世代を含む58モデルに対応。ワイルドカードでのモデル制限が可能に。
- **Partition Sorting**: パフォーマンス（速度）の下限を設定して、高速なプロバイダーを優先する機能。
- **Provider Explorer**: 全プロバイダーの統計（モデル数、独自モデル数など）を一括確認できる機能の追加。
- **ゲートウェイ高速化**: p99レイテンシが70%向上。

---

## 2. 詳細API仕様

### A. Partition Sorting (レイテンシ/スループット制御)
リクエスト時に `provider` オブジェクトでソート順や速度のしきい値を指定できます。

**JSON構造:**
```json
{
  "model": "...",
  "provider": {
    "sort": {
      "by": "price",       // "price", "throughput", "latency"
      "partition": "none"  // "model" (デフォルト) または "none" (複数モデル指定時にフラットに比較)
    },
    "preferred_min_throughput": {
      "p90": 50            // 90%の確率で50トークン/秒以上出るプロバイダーを優先
    },
    "preferred_max_latency": {
      "p50": 0.5           // 50%の確率で0.5秒以内にレスポンスが来るプロバイダーを優先
    }
  }
}
```
*※これらは「足切り（エラー）」ではなく「優先度（deprioritization）」として機能するため、条件を満たすプロバイダーがなくてもエラーにはならず、レイテンシのヒットもありません。*

### B. Auto Router のカスタマイズ (ワイルドカード制限)
`openrouter/auto` が選択するモデルを、`plugins` パラメータで制限できます。

**JSON構造:**
```json
{
  "model": "openrouter/auto",
  "plugins": [
    {
      "id": "auto-router",
      "allowed_models": [
        "anthropic/*",      // Anthropicの全モデル
        "openai/gpt-5*",    // GPT-5系すべて
        "*/claude-*"        // プロバイダー問わず名前に "claude-" を含むもの
      ]
    }
  ]
}
```

### C. プロバイダー情報の取得
モデルごとの詳細なプロバイダー（エンドポイント）情報は、個別APIで取得可能です。

- **モデル別エンドポイントAPI**: `https://openrouter.ai/api/v1/models/{model_id}/endpoints`
- **取得可能な情報**: `provider_name`, `quantization`, `uptime_last_30m`, `latency_last_30m` など。

---

## 3. 注目モデル (2026年1月時点)
- `anthropic/claude-opus-4.5`: エージェントワークフロー最適化の最新版。
- `openai/gpt-5.1` / `openai/gpt-5`: OpenAIの次世代フラグシップ。
- `x-ai/grok-4`: xAIの最新大規模モデル。
- `qwen/qwen3-235b`: Qwenシリーズの巨大モデル。

---

## 4. 便利なドキュメントリンク
- [Provider Routing / Partition Sorting](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Auto Router Customization](https://openrouter.ai/docs/guides/routing/routers/auto-router)
- [Provider Explorer](https://openrouter.ai/providers)
