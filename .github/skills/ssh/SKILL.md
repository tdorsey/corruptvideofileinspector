---
name: ssh
description: Skill for connecting to remote hosts via SSH, transferring files, and diagnosing SSH failures
---

# SSH Skill

This skill covers connecting to remote hosts, running remote commands, transferring files, and diagnosing SSH connectivity problems.

## When to Use

- Connecting to a remote server or VM to inspect or manage services
- Running commands on a remote host as part of a deployment or debug workflow
- Transferring files to or from a remote host
- Diagnosing SSH connection failures (key auth, host verification, timeouts)
- Setting up SSH tunnels or port forwarding

## Basic Connection

```bash
# Connect with default identity (~/.ssh/id_rsa or id_ed25519)
ssh user@host

# Specify a key file
ssh -i ~/.ssh/my_key user@host

# Specify a non-default port
ssh -p 2222 user@host

# Verbose output for debugging
ssh -v user@host      # basic
ssh -vvv user@host    # maximum verbosity
```

## Running Remote Commands

```bash
# Run a single command and return output locally
ssh user@host "docker ps -a"

# Run multiple commands in one session
ssh user@host "cd /app && docker compose logs --tail 50"

# Preserve local environment variables (use carefully)
ssh user@host "MY_VAR=$MY_VAR /app/script.sh"
```

## File Transfer

```bash
# Copy local file to remote
scp /local/path/file.txt user@host:/remote/path/

# Copy remote file to local
scp user@host:/remote/path/file.txt /local/path/

# Copy directory recursively
scp -r /local/dir user@host:/remote/path/

# rsync (preferred for large transfers — only sends diffs)
rsync -avz /local/dir/ user@host:/remote/path/
rsync -avz -e "ssh -p 2222" /local/dir/ user@host:/remote/path/
```

## SSH Config (~/.ssh/config)

Use `~/.ssh/config` to avoid repeating connection options:

```
Host myserver
    HostName 192.168.1.100
    User deploy
    Port 2222
    IdentityFile ~/.ssh/deploy_key
    ServerAliveInterval 60
```

Then simply: `ssh myserver`

## Key Management

```bash
# Generate a new ed25519 key pair (preferred over RSA)
ssh-keygen -t ed25519 -C "description" -f ~/.ssh/my_key

# Copy public key to remote host
ssh-copy-id -i ~/.ssh/my_key.pub user@host

# Manual equivalent of ssh-copy-id
cat ~/.ssh/my_key.pub | ssh user@host "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Check which key is being offered
ssh -v user@host 2>&1 | grep "Offering"

# List loaded keys in agent
ssh-add -l

# Add key to agent
ssh-add ~/.ssh/my_key
```

## Port Forwarding / Tunnels

```bash
# Local port forwarding: access remote service locally
# Access remote-host:5432 as localhost:5432
ssh -L 5432:localhost:5432 user@remote-host

# Remote port forwarding: expose local port on remote host
ssh -R 8080:localhost:3000 user@remote-host

# Dynamic SOCKS proxy
ssh -D 1080 user@remote-host

# Keep tunnel alive in background
ssh -fNL 5432:localhost:5432 user@remote-host
```

## Common Issues and Remedies

### Permission Denied (publickey)

1. Confirm the key is loaded: `ssh-add -l`
2. Add it if missing: `ssh-add ~/.ssh/my_key`
3. Verify the public key is in `~/.ssh/authorized_keys` on the remote host
4. Check permissions: remote `~/.ssh` must be `700`, `authorized_keys` must be `600`
5. Use `-v` to see which keys are being tried

### Host Key Verification Failed

```bash
# Remove stale host key (safe if you know the host changed)
ssh-keygen -R <hostname_or_ip>
```

### Connection Timeout / Refused

1. Verify the host is reachable: `ping host` or `nc -zv host 22`
2. Check the SSH port: `nc -zv host 2222`
3. On the remote: confirm `sshd` is running — `systemctl status sshd`
4. Check firewall rules: `sudo ufw status` or `sudo iptables -L`

### Too Many Authentication Failures

```bash
# Explicitly specify the key to avoid offering too many
ssh -o IdentitiesOnly=yes -i ~/.ssh/my_key user@host
```

### Slow Connection / Login Delay

```bash
# Disable DNS reverse lookup on server (/etc/ssh/sshd_config)
UseDNS no
# Then restart: sudo systemctl restart sshd
```

## SSH Hardening Checklist (for servers you manage)

- Disable password authentication: `PasswordAuthentication no`
- Disable root login: `PermitRootLogin no`
- Restrict to specific users: `AllowUsers deploy admin`
- Use a non-default port to reduce noise (optional)
- Enable `UseDNS no` to speed up connections

## Definition of Done

- Connection succeeds without manual passphrase entry (key in agent)
- Remote commands execute and return expected output
- Any connectivity errors are diagnosed with `-v` output and root cause identified
