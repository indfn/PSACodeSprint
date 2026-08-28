import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Shield, Key, Server, LogOut } from 'lucide-react';
import {
  adminLogin,
  adminGetConfig,
  adminInjectApiKey,
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

  const llm = config?.llm;
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

      {/* Current Config */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-xs">Current LLM Config</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-muted-foreground">Provider</span>
              <p className="font-medium">{llm?.provider || '--'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Model</span>
              <p className="font-medium">{llm?.model || '--'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Base URL</span>
              <p className="font-medium truncate">{llm?.base_url || '--'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">API Type</span>
              <p className="font-medium">{llm?.api_type || '--'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Key Env Var</span>
              <p className="font-medium">{llm?.api_key_env || '--'}</p>
            </div>
            <div>
              <span className="text-muted-foreground">Active Problem</span>
              <p className="font-medium">{config?.active_problem?.id || '--'}</p>
            </div>
          </div>

          {llm?.fallback_provider && (
            <div className="border-t pt-2 mt-2">
              <p className="text-xs font-medium text-muted-foreground mb-1">Fallback</p>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <span className="text-muted-foreground">Provider</span>
                  <p className="font-medium">{llm.fallback_provider}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Model</span>
                  <p className="font-medium">{llm.fallback_model || '--'}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Base URL</span>
                  <p className="font-medium truncate">{llm.fallback_base_url || '--'}</p>
                </div>
              </div>
            </div>
          )}

          {Object.keys(keyStatus).length > 0 && (
            <div className="border-t pt-2 mt-2">
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
