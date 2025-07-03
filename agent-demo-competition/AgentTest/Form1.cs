using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.DirectoryServices.ActiveDirectory;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using WebSocketSharp;


namespace AgentTest
{
	public partial class Form1 : Form
	{
		WebSocket? ws;
		bool textUpdating;
		public Form1()
		{
			InitializeComponent();
		}

		private void btnConnect_Click(object sender, EventArgs e)
		{
			ws = new WebSocket(tbUrl.Text);
			ws.OnOpen += Ws_OnOpen;
			ws.OnClose += Ws_OnClose;
			ws.OnMessage += Ws_OnMessage;
			ws.OnError += Ws_OnError;
			if (tbUrl.Text.StartsWith("wss"))
			{
				ws.SslConfiguration.EnabledSslProtocols = System.Security.Authentication.SslProtocols.Tls | System.Security.Authentication.SslProtocols.Tls12;
			}
			Task.Run(() => ws.Connect());
		}

		private void Ws_OnError(object? sender, WebSocketSharp.ErrorEventArgs e)
		{
			MessageBox.Show("Error: " + e.Message);
		}

		private void Ws_OnMessage(object? sender, MessageEventArgs e)
		{
			Invoke((MethodInvoker)delegate
			{
				listMain.Items.Add(new MessageItem("agent", e.Data));
			});
		}

		private void Ws_OnClose(object? sender, CloseEventArgs e)
		{
			Invoke((MethodInvoker)delegate
			{
				rbStatus.Checked = false;
				btnSend.Enabled = false;
			});
		}

		private void Ws_OnOpen(object? sender, EventArgs e)
		{
			Invoke((MethodInvoker)delegate
			{
				rbStatus.Checked = true;
				btnSend.Enabled = true;
			});
		}

		private void btnSend_Click(object sender, EventArgs e)
		{
			if (!Util.IsValidJson(tbRaw.Text))
			{
				MessageBox.Show("不是合法的Json", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
				return;
			}
			if (tbChat.Text.Length > 0)
			{
				tbChat.AutoCompleteCustomSource.Add(tbChat.Text);
			}
			if (tbCommand.Text.Length > 0)
			{
				tbCommand.AutoCompleteCustomSource.Add(tbCommand.Text);
			}
			Task.Run(() =>
			{
				ws?.Send(tbRaw.Text);
			});
			listMain.Items.Add(new MessageItem("me", tbRaw.Text));
		}

		private void tbChat_TextChanged(object sender, EventArgs e)
		{
			if (textUpdating) { return; }
			textUpdating = true;
			tbCommand.Text = "";
			AgentMessage msg = AgentMessage.CreateChat(tbChat.Text);
			tbRaw.Text = Util.SerializeMessage(msg);
			textUpdating = false;
		}

		private void tbCommand_TextChanged(object sender, EventArgs e)
		{
			if (textUpdating) { return; }
			textUpdating = true;
			tbChat.Text = "";
			AgentMessage msg = AgentMessage.CreateCommand(tbCommand.Text);
			tbRaw.Text = Util.SerializeMessage(msg);
			textUpdating = false;
		}

		private void tbRaw_TextChanged(object sender, EventArgs e)
		{
			if (textUpdating) { return; }
			textUpdating = true;
			tbCommand.Text = "";
			tbChat.Text = "";
			textUpdating = false;
		}

		private void listMain_SelectedIndexChanged(object sender, EventArgs e)
		{
			MessageItem item = (MessageItem)listMain.SelectedItem;
			if (item == null)
			{
				tbMain.Text = "";
				return;
			}
			try
			{
				tbMain.Text = Util.FormatJson(item.rawMessage);
			}
			catch (Exception ex)
			{
				tbMain.Text = item.rawMessage;
			}
			
		}
	}

	public class MessageItem
	{
		public string Speaker;
		public AgentMessage? message;
		public string rawMessage;
		public DateTime Time = DateTime.Now;
		public MessageItem(string speaker, AgentMessage msg)
		{
			Speaker = speaker;
			message = msg;
			rawMessage = Util.SerializeMessage(msg);
		}
		public MessageItem(string speaker, string raw)
		{
			Speaker = speaker;
			rawMessage = raw;
			message = Util.DeserializeMessage(raw);
		}
		public override string ToString()
		{
			string type;
			string agent;
			string content;
			if (message == null)
			{
				type = "invalid";
				agent = "null";
				content = rawMessage ?? "";
			}
			else
			{
				type = message.Type ?? "invalid";
				agent = message.Agent ?? "null";
				switch (message.Type)
				{
					case "chat":
						content = message.Text ?? "";
						break;
					case "command":
						content = message.Command ?? "";
						break;
					default:
						content = Util.SerializeMessage(message);
						break;
				}
			}
			return $"{Time:HH:mm:ss.fff} {Speaker}({type},{agent}): {content}";
		}
	}

	public static class Util
	{
		public static string SerializeMessage(AgentMessage msg)
		{
			return JsonConvert.SerializeObject(msg, new JsonSerializerSettings()
			{
				NullValueHandling = NullValueHandling.Ignore,
			});
		}
		public static AgentMessage? DeserializeMessage(string msg)
		{
			try
			{
				return JsonConvert.DeserializeObject<AgentMessage>(msg, new JsonSerializerSettings()
				{
				});
			}
			catch (Exception ex)
			{
				//MessageBox.Show("Error: " + ex);
				return null;
			}
		}
		public static bool IsValidJson(string s)
		{
			try
			{
				JObject.Parse(s);
				return true;
			}
			catch (JsonReaderException)
			{
				return false;
			}
		}
		public static string FormatJson(string json)
		{
			return JObject.Parse(json).ToString(Formatting.Indented);
		}
	}

	[Serializable]
	public class AgentMessage
	{
		[JsonProperty("type")]
		public string? Type;
		[JsonProperty("text")]
		public string? Text;
		[JsonProperty("agent")]
		public string? Agent;
		[JsonProperty("command")]
		public string? Command;
		[JsonProperty("data")]
		public object? Data;

		static public AgentMessage CreateChat(string text)
		{
			return new AgentMessage
			{
				Type = "chat",
				Text = text,
			};
		}
		static public AgentMessage CreateCommand(string command)
		{
			return CreateCommand(command, null);
		}
		static public AgentMessage CreateCommand(string command, object? data)
		{
			return new AgentMessage
			{
				Type = "command",
				Command = command,
				Data = data,
			};
		}
	}
}
