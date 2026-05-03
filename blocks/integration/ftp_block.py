"""
Bloco FTP/SFTP do PyFlow RPA.
Upload e download de arquivos via FTP (ftplib nativo) e SFTP (paramiko).
Coloque em: blocks/integration/ftp_block.py

Requisitos:
  FTP:  nativo do Python (ftplib)
  SFTP: pip install paramiko
"""
import os
import ftplib
from blocks.base_block import BaseBlock


class FtpBlock(BaseBlock):
    name        = "FTP / SFTP"
    description = "Transfere arquivos via FTP ou SFTP. Suporta upload, download, listar arquivos remotos e deletar arquivo remoto."
    category    = "Integração"

    params_schema = [
        {
            "name":        "protocol",
            "label":       "Protocolo",
            "type":        "str",
            "required":    True,
            "default":     "ftp",
            "placeholder": "ftp | sftp"
        },
        {
            "name":        "action",
            "label":       "Ação",
            "type":        "str",
            "required":    True,
            "default":     "upload",
            "placeholder": "upload | download | list | delete"
        },
        {
            "name":        "host",
            "label":       "Host / IP do servidor",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: ftp.meusite.com | 192.168.1.100"
        },
        {
            "name":        "port",
            "label":       "Porta",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "FTP=21 | SFTP=22 (vazio = padrão do protocolo)"
        },
        {
            "name":        "username",
            "label":       "Usuário",
            "type":        "str",
            "required":    True,
            "default":     "",
            "placeholder": "Ex: admin | anonymous"
        },
        {
            "name":        "password",
            "label":       "Senha",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Senha do usuário FTP/SFTP"
        },
        {
            "name":        "local_path",
            "label":       "Caminho local (arquivo ou pasta)",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: saida/relatorio.csv | downloads/arquivo.pdf"
        },
        {
            "name":        "remote_path",
            "label":       "Caminho remoto no servidor",
            "type":        "str",
            "required":    False,
            "default":     "",
            "placeholder": "Ex: /public/relatorio.csv | /home/user/arquivo.pdf"
        },
        {
            "name":        "variable_name",
            "label":       "Salvar resultado (list) como variável",
            "type":        "str",
            "required":    False,
            "default":     "ftp_lista",
            "placeholder": "Nome da variável para salvar a lista de arquivos remotos"
        },
        {
            "name":        "timeout",
            "label":       "Timeout em segundos",
            "type":        "str",
            "required":    False,
            "default":     "30",
            "placeholder": "30"
        },
    ]

    PROTOCOLS = {"ftp", "sftp"}
    ACTIONS   = {"upload", "download", "list", "delete"}

    def execute(self, params: dict) -> dict:
        errors = self.validate_params(params)
        if errors:
            return {"success": False, "message": "\n".join(errors)}

        protocol    = params.get("protocol", "ftp").strip().lower()
        action      = params.get("action", "upload").strip().lower()
        host        = params.get("host", "").strip()
        port_str    = params.get("port", "").strip()
        username    = params.get("username", "").strip()
        password    = params.get("password", "").strip()
        local_path  = params.get("local_path", "").strip()
        remote_path = params.get("remote_path", "").strip()
        var_name    = params.get("variable_name", "ftp_lista").strip() or "ftp_lista"

        try:
            timeout = int(params.get("timeout", 30))
        except ValueError:
            timeout = 30

        if protocol not in self.PROTOCOLS:
            return {"success": False, "message": f"Protocolo '{protocol}' inválido. Use: ftp, sftp"}
        if action not in self.ACTIONS:
            return {"success": False, "message": f"Ação '{action}' inválida. Use: upload, download, list, delete"}
        if not host:
            return {"success": False, "message": "host é obrigatório."}

        # Porta padrão por protocolo
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                return {"success": False, "message": f"port deve ser um número. Recebido: '{port_str}'"}
        else:
            port = 22 if protocol == "sftp" else 21

        if protocol == "ftp":
            return self._run_ftp(action, host, port, username, password,
                                 local_path, remote_path, var_name, timeout)
        else:
            return self._run_sftp(action, host, port, username, password,
                                  local_path, remote_path, var_name, timeout)

    # ── FTP ───────────────────────────────────────────────────────────

    def _run_ftp(self, action, host, port, username, password,
                 local_path, remote_path, var_name, timeout) -> dict:
        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(username, password)
        except ftplib.all_errors as e:
            return {"success": False, "message": f"Falha na conexão FTP: {str(e)}"}

        try:
            if action == "upload":
                return self._ftp_upload(ftp, local_path, remote_path)
            if action == "download":
                return self._ftp_download(ftp, local_path, remote_path)
            if action == "list":
                return self._ftp_list(ftp, remote_path, var_name)
            if action == "delete":
                return self._ftp_delete(ftp, remote_path)
        except ftplib.all_errors as e:
            return {"success": False, "message": f"Erro FTP: {str(e)}"}
        finally:
            try: ftp.quit()
            except Exception: pass

    def _ftp_upload(self, ftp, local_path, remote_path) -> dict:
        if not local_path:
            return {"success": False, "message": "local_path é obrigatório para upload."}
        if not os.path.exists(local_path):
            return {"success": False, "message": f"Arquivo local não encontrado: {local_path}"}
        remote = remote_path or os.path.basename(local_path)
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {remote}", f)
        size = os.path.getsize(local_path)
        return {"success": True, "message": f"Upload concluído: {local_path} → {remote} ({size:,} bytes)"}

    def _ftp_download(self, ftp, local_path, remote_path) -> dict:
        if not remote_path:
            return {"success": False, "message": "remote_path é obrigatório para download."}
        local = local_path or os.path.basename(remote_path)
        os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
        with open(local, "wb") as f:
            ftp.retrbinary(f"RETR {remote_path}", f.write)
        size = os.path.getsize(local)
        return {"success": True, "message": f"Download concluído: {remote_path} → {local} ({size:,} bytes)"}

    def _ftp_list(self, ftp, remote_path, var_name) -> dict:
        path = remote_path or "."
        files = ftp.nlst(path)
        from blocks.browser.extract_text import ExtractTextBlock
        ctx = ExtractTextBlock._context
        ctx[var_name]             = files
        ctx[f"{var_name}_total"]  = str(len(files))
        return {"success": True, "message": f"Listados {len(files)} item(s) em '{path}' → '{var_name}'"}

    def _ftp_delete(self, ftp, remote_path) -> dict:
        if not remote_path:
            return {"success": False, "message": "remote_path é obrigatório para delete."}
        ftp.delete(remote_path)
        return {"success": True, "message": f"Arquivo remoto removido: {remote_path}"}

    # ── SFTP ──────────────────────────────────────────────────────────

    def _run_sftp(self, action, host, port, username, password,
                  local_path, remote_path, var_name, timeout) -> dict:
        try:
            import paramiko
        except ImportError:
            return {"success": False, "message": "paramiko não instalado. Rode: pip install paramiko"}

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=port, username=username,
                           password=password, timeout=timeout)
            sftp = client.open_sftp()
        except Exception as e:
            return {"success": False, "message": f"Falha na conexão SFTP: {str(e)}"}

        try:
            if action == "upload":
                return self._sftp_upload(sftp, local_path, remote_path)
            if action == "download":
                return self._sftp_download(sftp, local_path, remote_path)
            if action == "list":
                return self._sftp_list(sftp, remote_path, var_name)
            if action == "delete":
                return self._sftp_delete(sftp, remote_path)
        except Exception as e:
            return {"success": False, "message": f"Erro SFTP: {str(e)}"}
        finally:
            try: sftp.close()
            except Exception: pass
            try: client.close()
            except Exception: pass

    def _sftp_upload(self, sftp, local_path, remote_path) -> dict:
        if not local_path:
            return {"success": False, "message": "local_path é obrigatório para upload."}
        if not os.path.exists(local_path):
            return {"success": False, "message": f"Arquivo local não encontrado: {local_path}"}
        remote = remote_path or os.path.basename(local_path)
        sftp.put(local_path, remote)
        size = os.path.getsize(local_path)
        return {"success": True, "message": f"Upload SFTP concluído: {local_path} → {remote} ({size:,} bytes)"}

    def _sftp_download(self, sftp, local_path, remote_path) -> dict:
        if not remote_path:
            return {"success": False, "message": "remote_path é obrigatório para download."}
        local = local_path or os.path.basename(remote_path)
        os.makedirs(os.path.dirname(local) or ".", exist_ok=True)
        sftp.get(remote_path, local)
        size = os.path.getsize(local)
        return {"success": True, "message": f"Download SFTP concluído: {remote_path} → {local} ({size:,} bytes)"}

    def _sftp_list(self, sftp, remote_path, var_name) -> dict:
        path  = remote_path or "."
        files = sftp.listdir(path)
        from blocks.browser.extract_text import ExtractTextBlock
        ctx = ExtractTextBlock._context
        ctx[var_name]            = files
        ctx[f"{var_name}_total"] = str(len(files))
        return {"success": True, "message": f"Listados {len(files)} item(s) em '{path}' → '{var_name}'"}

    def _sftp_delete(self, sftp, remote_path) -> dict:
        if not remote_path:
            return {"success": False, "message": "remote_path é obrigatório para delete."}
        sftp.remove(remote_path)
        return {"success": True, "message": f"Arquivo remoto removido (SFTP): {remote_path}"}
