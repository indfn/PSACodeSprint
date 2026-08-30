import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Shield, Key, Server, LogOut, Check } from 'lucide-react';
import {
  adminLogin,
  adminGetConfig,
  adminInjectApiKey,
  adminUpdateConfig,
  type AdminConfig,
} from '@/api/nexus';

export default function AdminPage() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Login form
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  // Config
  const [config, setConfig] = useState<AdminConfig | null>(null);

  // Editable LLM config
  const [llm, setLlm] = useState({
    provider: '',
    model: '',
    base_url: '',
    api_type: 'openai',
    api_key_env: '',
    fallback_provider: '',
    fallback_model: '',
    fallback_base_url: '',
    fallback_api_key_env: '',
  });
  const [saveMsg, setSaveMsg] = useState('');
  const [saveTimeout, setSaveTimeout] = useState<ReturnType<typeof setTimeout> | null>(null);

  // API key injection
  const [keyProvider, setKeyProvider] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [keyLoading, setKeyLoading] = useState(false);
  const [keyMsg, setKeyMsg] = useState('');
  const [keyMsgType, setKeyMsgType] = useState<'ok' | 'err'>('ok');

  async function tryLoadConfig() {
    try {
      const data = await adminGetConfig();
      setConfig(data);
      setLoggedIn(true);
      if (data.llm) {
        setLlm({
          provider: data.llm.provider || '',
          model: data.llm.model || '',
          base_url: data.llm.base_url || '',
          api_type: data.llm.api_type || 'openai',
          api_key_env: data.llm.api_key_env || '',
          fallback_provider: data.llm.fallback_provider || '',
          fallback_model: data.llm.fallback_model || '',
          fallback_base_url: data.llm.fallback_base_url || '',
          fallback_api_key_env: data.llm.fallback_api_key_env || '',
        });
      }
      if (!keyProvider && data.llm?.provider) {
        setKeyProvider(data.llm.provider);
      }
    } catch {
      // not logged in
    }
  }

  useEffect(() => {
    tryLoadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await adminLogin(username, password);
      setLoggedIn(true);
      const data = await adminGetConfig();
      setConfig(data);
      if (data.llm) {
        setLlm({
          provider: data.llm.provider || '',
          model: data.llm.model || '',
          base_url: data.llm.base_url || '',
          api_type: data.llm.api_type || 'openai',
          api_key_env: data.llm.api_key_env || '',
          fallback_provider: data.llm.fallback_provider || '',
          fallback_model: data.llm.fallback_model || '',
          fallback_base_url: data.llm.fallback_base_url || '',
          fallback_api_key_env: data.llm.fallback_api_key_env || '',
        });
      }
      if (!keyProvider && data.llm?.provider) {
        setKeyProvider(data.llm.provider);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await fetch('/api/admin/logout', { method: 'POST', credentials: 'same-origin' });
    } catch { /* ignore */ }
    document.cookie = 'psa_admin_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    setLoggedIn(false);
    setConfig(null);
    setUsername('');
    setPassword('');
  }

  function handleLlmChange(field: string, value: string) {
    setLlm((prev) => ({ ...prev, [field]: value }));
    // Debounce auto-save
    if (saveTimeout) clearTimeout(saveTimeout);
    const timeout = setTimeout(async () => {
      try {
        await adminUpdateConfig({ [field]: value });
        setSaveMsg('Saved');
        setTimeout(() => setSaveMsg(''), 2000);
      } catch {
        setSaveMsg('Save failed');
        setTimeout(() => setSaveMsg(''), 3000);
      }
    }, 500);
    setSaveTimeout(timeout);
  }

  async function handleInjectKey(e: React.FormEvent) {
    e.preventDefault();
    setKeyMsg('');
    if (!keyProvider.trim()) {
      setKeyMsg('Provider is required');
      setKeyMsgType('err');
      return;
    }
    if (!apiKey.trim()) {
      setKeyMsg('API key is required');
      setKeyMsgType('err');
      return;
    }
    setKeyLoading(true);
    try {
      const res = await adminInjectApiKey(keyProvider.trim(), apiKey.trim());
      setKeyMsg(res.message || 'Key injected');
      setKeyMsgType('ok');
      setApiKey('');
      const data = await adminGetConfig();
      setConfig(data);
    } catch (err) {
      setKeyMsg(err instanceof Error ? err.message : 'Injection failed');
      setKeyMsgType('err');
    } finally {
      setKeyLoading(false);
    }
  }

  if (!loggedIn) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Shield size={16} />
              Admin Login
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-3">
              {error && (
                <p className="text-xs text-destructive bg-destructive/10 px-3 py-2 rounded">
                  {error}
                </p>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="username" className="text-xs">
                  Username
                </Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="off"
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password" className="text-xs">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="off"
                  className="h-8 text-xs"
                />
              </div>
              <Button type="submit" disabled={loading} className="w-full h-8 text-xs">
                {loading ? 'Logging in...' : 'Login'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  const readiness = config?.provider_readiness;
  const keyStatus = config?.api_key_status || {};

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-bold">Admin Console</h1>
        <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-1.5 h-7 text-xs">
          <LogOut size={14} />
          Logout
        </Button>
      </div>

      {/* Provider Readiness */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs flex items-center gap-2">
            <Server size={14} />
            Provider Readiness
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                readiness?.ready ? 'bg-emerald-500' : 'bg-red-500'
              }`}
            />
            <span className="text-xs">{readiness?.message || 'Unknown'}</span>
          </div>
        </CardContent>
      </Card>

      {/* API Key Injection */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs flex items-center gap-2">
            <Key size={14} />
            API Key Injection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleInjectKey} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Provider</Label>
                <Input
                  value={keyProvider}
                  onChange={(e) => setKeyProvider(e.target.value)}
                  placeholder="anthropic, openai, gemini..."
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">API Key</Label>
                <Input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="h-8 text-xs"
                />
              </div>
            </div>
            {keyMsg && (
              <p
                className={`text-xs ${
                  keyMsgType === 'ok' ? 'text-emerald-500' : 'text-destructive'
                }`}
              >
                {keyMsg}
              </p>
            )}
            <Button type="submit" disabled={keyLoading} size="sm" className="h-7 text-xs">
              {keyLoading ? 'Injecting...' : 'Inject Key'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* LLM Config Editor */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs">LLM Configuration</CardTitle>
            {saveMsg && (
              <span className={`text-[10px] flex items-center gap-1 ${saveMsg === 'Saved' ? 'text-emerald-500' : 'text-destructive'}`}>
                {saveMsg === 'Saved' && <Check size={10} />}
                {saveMsg}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Primary Config */}
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Primary</p>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-[10px]">Provider</Label>
                <select
                  value={llm.provider}
                  onChange={(e) => handleLlmChange('provider', e.target.value)}
                  className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-xs"
                >
                  <option value="anthropic">Anthropic</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Gemini</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="ollama">Ollama</option>
                  <option value="vllm">vLLM</option>
                  <option value="lmstudio">LM Studio</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Model</Label>
                <Input
                  value={llm.model}
                  onChange={(e) => handleLlmChange('model', e.target.value)}
                  placeholder="claude-sonnet-4-20250514"
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Base URL</Label>
                <Input
                  value={llm.base_url}
                  onChange={(e) => handleLlmChange('base_url', e.target.value)}
                  placeholder="https://api.anthropic.com (leave empty for default)"
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">API Type</Label>
                <select
                  value={llm.api_type}
                  onChange={(e) => handleLlmChange('api_type', e.target.value)}
                  className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-xs"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="google">Google</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">API Key Env Var</Label>
                <Input
                  value={llm.api_key_env}
                  onChange={(e) => handleLlmChange('api_key_env', e.target.value)}
                  placeholder="ANTHROPIC_API_KEY"
                  className="h-8 text-xs"
                />
              </div>
            </div>
          </div>

          {/* Fallback Config */}
          <div className="border-t pt-3 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Fallback</p>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-[10px]">Provider</Label>
                <select
                  value={llm.fallback_provider}
                  onChange={(e) => handleLlmChange('fallback_provider', e.target.value)}
                  className="h-8 w-full rounded-md border border-input bg-transparent px-2 text-xs"
                >
                  <option value="">None</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Gemini</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="ollama">Ollama</option>
                  <option value="vllm">vLLM</option>
                  <option value="lmstudio">LM Studio</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Model</Label>
                <Input
                  value={llm.fallback_model}
                  onChange={(e) => handleLlmChange('fallback_model', e.target.value)}
                  placeholder="gpt-4o"
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">Base URL</Label>
                <Input
                  value={llm.fallback_base_url}
                  onChange={(e) => handleLlmChange('fallback_base_url', e.target.value)}
                  placeholder="leave empty for default"
                  className="h-8 text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-[10px]">API Key Env Var</Label>
                <Input
                  value={llm.fallback_api_key_env}
                  onChange={(e) => handleLlmChange('fallback_api_key_env', e.target.value)}
                  placeholder="OPENAI_API_KEY"
                  className="h-8 text-xs"
                />
              </div>
            </div>
          </div>

          {/* API Key Status */}
          {Object.keys(keyStatus).length > 0 && (
            <div className="border-t pt-2">
              <p className="text-xs font-medium text-muted-foreground mb-1">API Key Status</p>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(keyStatus).map(([k, v]) => (
                  <Badge key={k} variant="outline" className="text-[10px]">
                    {k}: {v}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
