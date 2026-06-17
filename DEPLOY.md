# ArbitLens — Production-readiness no VM

## 1. Abrir porta 5000 no firewall GCP

**Cole no seu terminal local (com gcloud logado):**

```bash
# Criar regra pra abrir porta 5000 do mundo pro VM
gcloud compute firewall-rules create allow-arbitlens-5000 \
  --direction=INGRESS \
  --priority=1000 \
  --network=default \
  --action=ALLOW \
  --rules=tcp:5000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=http-server
```

Se o VM não tem tag `http-server`, adicionar:
```bash
gcloud compute instances add-tags hermes-1 \
  --tags http-server \
  --zone=us-central1-a
```

## 2. Testar acesso externo

```bash
curl http://34.30.146.117:5000/api/health
# Deve retornar: {"status":"healthy","database":"connected","version":"0.2.0"}
```

## 3. (Opcional) Adicionar HTTPS com Caddy

```bash
# Instalar Caddy (auto SSL via Let's Encrypt)
sudo apt install -y caddy

# /etc/caddy/Caddyfile
echo 'arbt.ly, www.arbt.ly {
    reverse_proxy localhost:5000
}' | sudo tee /etc/caddy/Caddyfile

# Apontar DNS A record: arbt.ly → 34.30.146.117
sudo systemctl reload caddy
```

## 4. Hardening mínimo

```bash
# Trocar senha DB padrão, mover pra secret manager
# Rate limit no FastAPI (slowapi)
# Backup diário do DB (já tem cron? verificar)
```

## Custo
- $0/mês extra (VM atual + firewall é free)
- Caddy + Let's Encrypt: free
- Domínio arbt.ly: ~R$50/ano

## Tempo estimado
- Firewall: 2 minutos
- Teste: 1 minuto  
- HTTPS (Caddy): 5 minutos + espera DNS propagar