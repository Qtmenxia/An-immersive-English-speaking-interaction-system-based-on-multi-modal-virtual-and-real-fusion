namespace AgentTest
{
	partial class Form1
	{
		/// <summary>
		/// 必需的设计器变量。
		/// </summary>
		private System.ComponentModel.IContainer components = null;

		/// <summary>
		/// 清理所有正在使用的资源。
		/// </summary>
		/// <param name="disposing">如果应释放托管资源，为 true；否则为 false。</param>
		protected override void Dispose(bool disposing)
		{
			if (disposing && (components != null))
			{
				components.Dispose();
			}
			base.Dispose(disposing);
		}

		#region Windows 窗体设计器生成的代码

		/// <summary>
		/// 设计器支持所需的方法 - 不要修改
		/// 使用代码编辑器修改此方法的内容。
		/// </summary>
		private void InitializeComponent()
		{
			tbMain = new TextBox();
			tbUrl = new TextBox();
			btnConnect = new Button();
			rbStatus = new RadioButton();
			tbChat = new TextBox();
			label1 = new Label();
			label2 = new Label();
			btnSend = new Button();
			tbRaw = new TextBox();
			label3 = new Label();
			tbCommand = new TextBox();
			listMain = new ListBox();
			splitContainer1 = new SplitContainer();
			((System.ComponentModel.ISupportInitialize)splitContainer1).BeginInit();
			splitContainer1.Panel1.SuspendLayout();
			splitContainer1.Panel2.SuspendLayout();
			splitContainer1.SuspendLayout();
			SuspendLayout();
			// 
			// tbMain
			// 
			tbMain.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
			tbMain.Font = new Font("微软雅黑", 9F, FontStyle.Regular, GraphicsUnit.Point);
			tbMain.Location = new Point(3, 4);
			tbMain.Margin = new Padding(3, 4, 3, 4);
			tbMain.Multiline = true;
			tbMain.Name = "tbMain";
			tbMain.ReadOnly = true;
			tbMain.ScrollBars = ScrollBars.Vertical;
			tbMain.Size = new Size(289, 435);
			tbMain.TabIndex = 0;
			// 
			// tbUrl
			// 
			tbUrl.Location = new Point(14, 16);
			tbUrl.Margin = new Padding(3, 4, 3, 4);
			tbUrl.Name = "tbUrl";
			tbUrl.Size = new Size(677, 31);
			tbUrl.TabIndex = 1;
			tbUrl.Text = "wss://echo.websocket.org";
			// 
			// btnConnect
			// 
			btnConnect.Location = new Point(699, 13);
			btnConnect.Margin = new Padding(3, 4, 3, 4);
			btnConnect.Name = "btnConnect";
			btnConnect.Size = new Size(84, 33);
			btnConnect.TabIndex = 2;
			btnConnect.Text = "连接";
			btnConnect.UseVisualStyleBackColor = true;
			btnConnect.Click += btnConnect_Click;
			// 
			// rbStatus
			// 
			rbStatus.AutoSize = true;
			rbStatus.Location = new Point(789, 17);
			rbStatus.Margin = new Padding(3, 4, 3, 4);
			rbStatus.Name = "rbStatus";
			rbStatus.Size = new Size(71, 28);
			rbStatus.TabIndex = 3;
			rbStatus.TabStop = true;
			rbStatus.Text = "状态";
			rbStatus.UseVisualStyleBackColor = true;
			// 
			// tbChat
			// 
			tbChat.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			tbChat.AutoCompleteMode = AutoCompleteMode.Suggest;
			tbChat.AutoCompleteSource = AutoCompleteSource.CustomSource;
			tbChat.Location = new Point(100, 525);
			tbChat.Margin = new Padding(3, 4, 3, 4);
			tbChat.Name = "tbChat";
			tbChat.Size = new Size(457, 31);
			tbChat.TabIndex = 4;
			tbChat.TextChanged += tbChat_TextChanged;
			// 
			// label1
			// 
			label1.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			label1.AutoSize = true;
			label1.Location = new Point(44, 528);
			label1.Name = "label1";
			label1.RightToLeft = RightToLeft.Yes;
			label1.Size = new Size(50, 24);
			label1.TabIndex = 6;
			label1.Text = "Chat";
			// 
			// label2
			// 
			label2.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			label2.AutoSize = true;
			label2.Location = new Point(2, 569);
			label2.Name = "label2";
			label2.RightToLeft = RightToLeft.Yes;
			label2.Size = new Size(100, 24);
			label2.TabIndex = 9;
			label2.Text = "Command";
			// 
			// btnSend
			// 
			btnSend.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			btnSend.Enabled = false;
			btnSend.Location = new Point(572, 637);
			btnSend.Margin = new Padding(3, 4, 3, 4);
			btnSend.Name = "btnSend";
			btnSend.Size = new Size(84, 56);
			btnSend.TabIndex = 8;
			btnSend.Text = "发送";
			btnSend.UseVisualStyleBackColor = true;
			btnSend.Click += btnSend_Click;
			// 
			// tbRaw
			// 
			tbRaw.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			tbRaw.AutoCompleteMode = AutoCompleteMode.Suggest;
			tbRaw.AutoCompleteSource = AutoCompleteSource.HistoryList;
			tbRaw.Location = new Point(99, 605);
			tbRaw.Margin = new Padding(3, 4, 3, 4);
			tbRaw.Multiline = true;
			tbRaw.Name = "tbRaw";
			tbRaw.Size = new Size(457, 117);
			tbRaw.TabIndex = 7;
			tbRaw.TextChanged += tbRaw_TextChanged;
			// 
			// label3
			// 
			label3.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			label3.AutoSize = true;
			label3.Location = new Point(47, 607);
			label3.Name = "label3";
			label3.RightToLeft = RightToLeft.Yes;
			label3.Size = new Size(46, 24);
			label3.TabIndex = 10;
			label3.Text = "Raw";
			// 
			// tbCommand
			// 
			tbCommand.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
			tbCommand.AutoCompleteMode = AutoCompleteMode.Suggest;
			tbCommand.AutoCompleteSource = AutoCompleteSource.CustomSource;
			tbCommand.Location = new Point(100, 566);
			tbCommand.Margin = new Padding(3, 4, 3, 4);
			tbCommand.Name = "tbCommand";
			tbCommand.Size = new Size(457, 31);
			tbCommand.TabIndex = 11;
			tbCommand.TextChanged += tbCommand_TextChanged;
			// 
			// listMain
			// 
			listMain.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
			listMain.Font = new Font("微软雅黑", 9F, FontStyle.Regular, GraphicsUnit.Point);
			listMain.FormattingEnabled = true;
			listMain.ItemHeight = 24;
			listMain.Location = new Point(3, 4);
			listMain.Margin = new Padding(3, 4, 3, 4);
			listMain.Name = "listMain";
			listMain.Size = new Size(563, 460);
			listMain.TabIndex = 12;
			listMain.SelectedIndexChanged += listMain_SelectedIndexChanged;
			// 
			// splitContainer1
			// 
			splitContainer1.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
			splitContainer1.Location = new Point(15, 57);
			splitContainer1.Margin = new Padding(3, 4, 3, 4);
			splitContainer1.Name = "splitContainer1";
			// 
			// splitContainer1.Panel1
			// 
			splitContainer1.Panel1.Controls.Add(listMain);
			// 
			// splitContainer1.Panel2
			// 
			splitContainer1.Panel2.Controls.Add(tbMain);
			splitContainer1.Size = new Size(872, 445);
			splitContainer1.SplitterDistance = 571;
			splitContainer1.TabIndex = 13;
			// 
			// Form1
			// 
			AutoScaleDimensions = new SizeF(11F, 24F);
			AutoScaleMode = AutoScaleMode.Font;
			ClientSize = new Size(900, 742);
			Controls.Add(splitContainer1);
			Controls.Add(tbCommand);
			Controls.Add(label3);
			Controls.Add(label2);
			Controls.Add(btnSend);
			Controls.Add(tbRaw);
			Controls.Add(label1);
			Controls.Add(tbChat);
			Controls.Add(rbStatus);
			Controls.Add(btnConnect);
			Controls.Add(tbUrl);
			Font = new Font("微软雅黑", 9F, FontStyle.Regular, GraphicsUnit.Point);
			Margin = new Padding(3, 4, 3, 4);
			Name = "Form1";
			Text = "Agent测试";
			splitContainer1.Panel1.ResumeLayout(false);
			splitContainer1.Panel2.ResumeLayout(false);
			splitContainer1.Panel2.PerformLayout();
			((System.ComponentModel.ISupportInitialize)splitContainer1).EndInit();
			splitContainer1.ResumeLayout(false);
			ResumeLayout(false);
			PerformLayout();
		}

		#endregion

		private System.Windows.Forms.TextBox tbMain;
		private System.Windows.Forms.TextBox tbUrl;
		private System.Windows.Forms.Button btnConnect;
		private System.Windows.Forms.RadioButton rbStatus;
		private System.Windows.Forms.TextBox tbChat;
		private System.Windows.Forms.Label label1;
		private System.Windows.Forms.Label label2;
		private System.Windows.Forms.Button btnSend;
		private System.Windows.Forms.TextBox tbRaw;
		private System.Windows.Forms.Label label3;
		private System.Windows.Forms.TextBox tbCommand;
		private System.Windows.Forms.ListBox listMain;
		private System.Windows.Forms.SplitContainer splitContainer1;
	}
}

