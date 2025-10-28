# === PATCH DE LOGGING - ADICIONAR NO INÍCIO DO app.py ===
import sys
import logging

# Configurar stdout para UTF-8 imediatamente
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Override do handler de logging para suportar Unicode
class UnicodeLoggingHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            if hasattr(self.stream, 'buffer'):
                # Usar buffer binário para UTF-8
                self.stream.buffer.write(msg.encode('utf-8') + self.terminator.encode('utf-8'))
            else:
                # Fallback
                self.stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fallback: remover caracteres Unicode problemáticos
            try:
                msg = self.format(record).encode('ascii', 'ignore').decode('ascii')
                self.stream.write(msg + self.terminator)
                self.flush()
            except:
                pass
        except:
            self.handleError(record)

# Substituir o handler padrão
logging._defaultHandler = UnicodeLoggingHandler()
